import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class TokenService {
  private readonly TOKEN_KEY = 'access_token';
  
  public isAuthenticated = signal<boolean>(this.hasToken());

  constructor() {
    console.log('[DEBUG] TokenService initialized');
    if (this.hasToken()) {
      console.log('[DEBUG] JWT Loaded from localStorage');
    }
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
    this.isAuthenticated.set(true);
  }

  removeToken(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    this.isAuthenticated.set(false);
  }

  hasToken(): boolean {
    return !!this.getToken();
  }
}
