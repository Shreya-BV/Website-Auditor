import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuditService } from '../../services/audit.service';

@Component({
  selector: 'app-home',
  imports: [CommonModule, FormsModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
})
export class HomeComponent {
  url = '';
  isLoading = false;
  errorMessage = '';
  loadingProgressText = 'Connecting to server...';
  
  private auditService = inject(AuditService);
  private router = inject(Router);

  private loadingSteps = [
    'Initializing audit engine...',
    'Fetching remote HTML contents...',
    'Auditing measurement tracking codes...',
    'Scanning advertising retargeting tags...',
    'Analyzing conversion forms and widgets...',
    'Checking SSL certificates and trust indicators...',
    'Running SEO and AI search discoverability checks...',
    'Compiling audit recommendations...',
    'Saving cache report results...'
  ];

  scanWebsite() {
    this.errorMessage = '';
    
    // Simple URL validation
    let targetUrl = this.url.trim();
    if (!targetUrl) {
      this.errorMessage = 'Please enter a website URL.';
      return;
    }

    // Normalize URL for validation
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      targetUrl = 'https://' + targetUrl;
    }

    try {
      const parsed = new URL(targetUrl);
      const hostname = parsed.hostname;
      if (!hostname || !hostname.includes('.')) {
        this.errorMessage = 'Please enter a valid domain (e.g. example.com).';
        return;
      }
    } catch {
      this.errorMessage = 'Invalid URL format. Please try again.';
      return;
    }

    // Start scanning
    this.isLoading = true;
    let stepIndex = 0;
    this.loadingProgressText = this.loadingSteps[0];

    // Cycle through loading steps to provide a premium UX
    const interval = setInterval(() => {
      if (stepIndex < this.loadingSteps.length - 1) {
        stepIndex++;
        this.loadingProgressText = this.loadingSteps[stepIndex];
      }
    }, 700);

    this.auditService.scanWebsite(this.url).subscribe({
      next: (report) => {
        clearInterval(interval);
        this.isLoading = false;
        if (report && (report.id || (report as any)._id)) {
          this.router.navigate(['/report', report.id || (report as any)._id]);
        } else {
          this.errorMessage = 'Failed to generate report details. Please try again.';
        }
      },
      error: (err) => {
        clearInterval(interval);
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'An error occurred while scanning the website. Please check the URL and try again.';
      }
    });
  }
}
