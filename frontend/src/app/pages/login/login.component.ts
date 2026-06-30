import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule, 
    RouterLink,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatCheckboxModule,
    MatSnackBarModule
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private snackBar = inject(MatSnackBar);

  hidePassword = true;
  isLoading = false;
  errorMessage = '';

  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    rememberMe: [false]
  });

  onSubmit() {
    if (this.loginForm.invalid) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    const { email, password, rememberMe } = this.loginForm.value;

    // Collect analytics data
    const screen_resolution = `${window.screen.width}x${window.screen.height}`;
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const language = navigator.language;
    const browser = this.getBrowserName();
    const operating_system = this.getOSName();

    const payload = {
      email,
      password,
      remember_me: rememberMe || false,
      browser,
      operating_system,
      screen_resolution,
      timezone,
      language
    };

    this.authService.login(payload).subscribe({
      next: () => {
        this.snackBar.open('Login successful! Redirecting...', 'Close', { duration: 3000, panelClass: ['success-snackbar'] });
        const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';
        setTimeout(() => this.router.navigateByUrl(returnUrl), 1000);
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Login failed. Please check your credentials.';
        this.snackBar.open(this.errorMessage, 'Close', { duration: 4000, panelClass: ['error-snackbar'] });
      }
    });
  }

  private getBrowserName(): string {
    const agent = window.navigator.userAgent.toLowerCase();
    if (agent.includes('edge') || agent.includes('edg')) return 'Edge';
    if (agent.includes('opr') || agent.includes('opera')) return 'Opera';
    if (agent.includes('chrome')) return 'Chrome';
    if (agent.includes('firefox')) return 'Firefox';
    if (agent.includes('safari')) return 'Safari';
    return 'Unknown';
  }

  private getOSName(): string {
    const agent = window.navigator.userAgent.toLowerCase();
    if (agent.includes('win')) return 'Windows';
    if (agent.includes('mac')) return 'MacOS';
    if (agent.includes('linux')) return 'Linux';
    if (agent.includes('android')) return 'Android';
    if (agent.includes('ios') || agent.includes('iphone')) return 'iOS';
    return 'Unknown';
  }
}
