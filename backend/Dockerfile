# Use the official Microsoft Playwright Python image (Ubuntu Jammy based)
# This completely eliminates the need for Nixpacks or manual apt-get dependency hunting.
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies (including FastAPI, Motor, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# The base image already has browsers installed, but to be absolutely sure
# we match the python package version to the browser version:
RUN playwright install chromium

# Copy the rest of the backend application code
COPY . .

# Start the FastAPI server using the dynamically assigned Railway $PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
