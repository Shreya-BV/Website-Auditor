import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap, catchError, of, throwError } from 'rxjs';
import { environment } from '../../environments/environment';

export interface User {
  id?: string;
  _id?: string;
  full_name: string;
  email: string;
  account_status?: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  
  private apiUrl = `${environment.apiUrl}/auth`;
  
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  
  public isAuthenticated = signal<boolean>(false);

  constructor() {
    this.checkInitialAuth();
  }

  private checkInitialAuth() {
    const token = this.getToken();
    if (token) {
      this.isAuthenticated.set(true);
      this.fetchCurrentUser().subscribe();
    }
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  setToken(token: string) {
    localStorage.setItem('access_token', token);
    this.isAuthenticated.set(true);
  }

  removeToken() {
    localStorage.removeItem('access_token');
    this.isAuthenticated.set(false);
    this.currentUserSubject.next(null);
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/register`, userData);
  }

  login(credentials: any): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials).pipe(
      tap(response => {
        if (response && response.access_token) {
          this.setToken(response.access_token);
          this.currentUserSubject.next(response.user);
        }
      })
    );
  }

  logout() {
    // Optional: Call backend logout if you want
    this.http.post(`${this.apiUrl}/logout`, {}).subscribe({
      next: () => this.handleLogoutSuccess(),
      error: () => this.handleLogoutSuccess() // Log out locally even if API fails
    });
  }

  private handleLogoutSuccess() {
    this.removeToken();
    this.router.navigate(['/login']);
  }

  fetchCurrentUser(): Observable<User | null> {
    if (!this.getToken()) {
      return of(null);
    }
    
    return this.http.get<User>(`${this.apiUrl}/me`).pipe(
      tap(user => {
        this.currentUserSubject.next(user);
        this.isAuthenticated.set(true);
      }),
      catchError(err => {
        console.error('Error fetching current user:', err);
        // If unauthorized, token is likely expired or invalid
        if (err.status === 401 || err.status === 403) {
          this.removeToken();
        }
        return throwError(() => err);
      })
    );
  }

  get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }
}
