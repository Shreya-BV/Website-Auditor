import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { TokenService } from '../services/token.service';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { Router } from '@angular/router';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const tokenService = inject(TokenService);
  const router = inject(Router);
  const token = tokenService.getToken();

  // Clone the request to add the authentication header.
  let authReq = req;
  if (token) {
    console.log(`[DEBUG] Interceptor Executed. Adding Authorization header.`);
    authReq = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`)
    });
  }

  // Pass on the cloned request instead of the original request.
  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // If we get a 401 Unauthorized error from the backend, log the user out
      if (error.status === 401) {
        tokenService.removeToken();
        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};
