import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { TokenService } from '../services/token.service';

export const authGuard: CanActivateFn = (route, state) => {
  const tokenService = inject(TokenService);
  const router = inject(Router);

  if (tokenService.hasToken()) {
    return true;
  }

  // Store the attempted URL for redirecting
  // But for now, just redirect to login
  router.navigate(['/login'], { queryParams: { returnUrl: state.url }});
  return false;
};
