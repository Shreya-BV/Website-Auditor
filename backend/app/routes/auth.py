from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timezone
import jwt
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

from app.database.mongodb import get_database
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.login_history import LoginHistory
from app.core.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def serialize_doc(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_database)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise credentials_exception
        
    user = await db["users"].find_one({"_id": oid})
    if user is None:
        raise credentials_exception
        
    return user

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db=Depends(get_database)):
    # Check if user exists
    existing_user = await db["users"].find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    password_hash = get_password_hash(user.password)
    new_user = {
        "full_name": user.full_name,
        "email": user.email.lower(),
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "last_login": None,
        "login_count": 0,
        "status": "Active"
    }
    
    result = await db["users"].insert_one(new_user)
    new_user["_id"] = result.inserted_id
    return serialize_doc(new_user)

@router.post("/login", response_model=Token)
async def login(user_login: UserLogin, request: Request, db=Depends(get_database)):
    logger.info(f"Step 1: Received login request for email: '{user_login.email}'")
    logger.info(f"Step 1b: Email type: {type(user_login.email)}, raw payload: {user_login.dict()}")
    
    # Trim and lower the email for robust matching
    search_email = user_login.email.strip().lower()
    logger.info(f"Step 2: Searching user with email: '{search_email}'")
    
    user = await db["users"].find_one({"email": search_email})
    
    if not user:
        logger.warning(f"Login failed: User not found for email '{search_email}'")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    logger.info(f"Step 3: User found with ID {user['_id']}. Checking password fields...")
    
    password_hash = user.get("password_hash")
    legacy_hashed_password = user.get("hashed_password")
    legacy_password = user.get("password")
    
    logger.info(f"Step 3b: password_hash exists: {bool(password_hash)}, legacy_hashed_password exists: {bool(legacy_hashed_password)}, legacy_password exists: {bool(legacy_password)}")
    
    needs_migration = False
    is_valid = False
    current_hash = password_hash or legacy_hashed_password
    
    if current_hash:
        logger.info(f"Step 4: Verifying against hash...")
        # Check if it's a valid bcrypt hash format
        if current_hash.startswith("$2b$") or current_hash.startswith("$2a$"):
            if verify_password(user_login.password, current_hash):
                is_valid = True
                if not password_hash:
                    needs_migration = True
                    password_hash = current_hash
                logger.info("Step 4b: Password verification against hash PASSED")
            else:
                logger.warning("Step 4b: Password verification against hash FAILED")
        else:
            # It's an invalid hash (likely plain text stored incorrectly)
            logger.warning(f"Step 4b: hash for user {user['_id']} is not a valid bcrypt hash. Checking as plain text.")
            if current_hash == user_login.password:
                is_valid = True
                needs_migration = True
                password_hash = get_password_hash(user_login.password)
                logger.info("Step 4b: Password verification against plain-text hash PASSED. Will migrate.")
            else:
                logger.warning("Step 4b: Password verification against plain-text hash FAILED")
    elif legacy_password:
        logger.info(f"Step 4: Verifying against legacy_password...")
        # Check if the legacy password is a bcrypt hash
        if legacy_password.startswith("$2b$") or legacy_password.startswith("$2a$"):
            if verify_password(user_login.password, legacy_password):
                is_valid = True
                needs_migration = True
                password_hash = legacy_password
                logger.info("Step 4b: Password verification against legacy bcrypt PASSED")
            else:
                logger.warning("Step 4b: Password verification against legacy bcrypt FAILED")
        else:
            # It's a plain-text password
            if legacy_password == user_login.password:
                is_valid = True
                needs_migration = True
                password_hash = get_password_hash(legacy_password)
                logger.info("Step 4b: Password verification against plain-text legacy PASSED")
            else:
                logger.warning("Step 4b: Password verification against plain-text legacy FAILED")
                
    if not is_valid:
        logger.warning(f"Login failed: Password verification failed for user {user['_id']}")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    if needs_migration:
        logger.info(f"Migrating legacy password to password_hash for user {user['_id']}")
        await db["users"].update_one(
            {"_id": user["_id"]},
            {"$set": {"password_hash": password_hash}, "$unset": {"password": "", "hashed_password": ""}}
        )
        user["password_hash"] = password_hash
        
    status_field = user.get("status") or user.get("account_status")
    if status_field != "Active":
        logger.warning(f"Login failed: Account is disabled for user {user['_id']}")
        raise HTTPException(status_code=403, detail="Account is disabled")

    logger.info(f"Step 5: Password verification passed for user {user['_id']}")

    # Generate JWT
    access_token = create_access_token(data={"sub": str(user["_id"]), "email": user["email"]})
    
    # Update user login stats (and map legacy fields for memory representation)
    if "created_date" in user and "created_at" not in user:
        user["created_at"] = user.pop("created_date")
    if "account_status" in user and "status" not in user:
        user["status"] = user.pop("account_status")
    if "created_at" not in user:
        user["created_at"] = datetime.now(timezone.utc)
    if "updated_at" not in user:
        user["updated_at"] = datetime.now(timezone.utc)

    user["last_login"] = datetime.now(timezone.utc)
    user["login_count"] = user.get("login_count", 0) + 1

    await db["users"].update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "last_login": user["last_login"], 
            "login_count": user["login_count"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
            "status": user["status"]
         }, "$unset": {"created_date": "", "account_status": ""}}
    )
    
    # Log visitor information
    ip_address = request.headers.get("x-forwarded-for")
    if ip_address:
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else "127.0.0.1"
        
    user_agent = request.headers.get("user-agent", "")
    
    # Basic parsing for browser and OS from user-agent (simplified)
    browser = "Unknown"
    os_name = "Unknown"
    if "Chrome" in user_agent: browser = "Chrome"
    elif "Firefox" in user_agent: browser = "Firefox"
    elif "Safari" in user_agent and "Chrome" not in user_agent: browser = "Safari"
    elif "Edge" in user_agent: browser = "Edge"
    
    if "Windows" in user_agent: os_name = "Windows"
    elif "Mac" in user_agent: os_name = "MacOS"
    elif "Linux" in user_agent: os_name = "Linux"
    elif "Android" in user_agent: os_name = "Android"
    elif "iOS" in user_agent or "iPhone" in user_agent: os_name = "iOS"
    
    login_record = {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "login_time": datetime.now(timezone.utc),
        "logout_time": None,
        "session_id": access_token[-20:],
        "ip_address": ip_address,
        "browser": user_login.browser or browser,
        "browser_version": user_login.browser_version or "Unknown",
        "operating_system": user_login.operating_system or os_name,
        "device_type": user_login.device_type or ("Mobile" if "Mobi" in user_agent else "Desktop"),
        "screen_resolution": user_login.screen_resolution or "Unknown",
        "timezone": user_login.timezone or "Unknown",
        "language": user_login.language or "Unknown",
        "country": "Unknown",
        "referrer": request.headers.get("referer", ""),
        "remember_me": user_login.remember_me,
        "login_status": "Success"
    }
    await db["login_history"].insert_one(login_record)
    
    user["_id"] = str(user["_id"])
    logger.info(f"JWT generated and login successful for user {user['_id']}")
    return {"access_token": access_token, "token_type": "bearer", "user": serialize_doc(user)}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return serialize_doc(current_user)

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    # Since we are using stateless JWTs, we just return success.
    # The frontend is responsible for deleting the token from localStorage.
    return {"success": True, "message": "Logged out successfully."}
