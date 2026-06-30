import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuditService } from '../../services/audit.service';

@Component({
  selector: 'app-audit-report-details',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './audit-report-details.component.html',
  styleUrl: './audit-report-details.component.scss'
})
export class AuditReportDetailsComponent implements OnInit {
  reportId = '';
  report: any = null;
  isLoading = true;
  errorMessage = '';
  isDownloading = false;

  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private auditService = inject(AuditService);

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.reportId = id;
        this.loadReport(id);
      } else {
        this.errorMessage = 'No report ID provided.';
        this.isLoading = false;
      }
    });
  }

  loadReport(id: string) {
    this.isLoading = true;
    this.errorMessage = '';
    this.auditService.getAuditReportDetails(id).subscribe({
      next: (data) => {
        this.report = data;
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Audit report not available.';
        this.isLoading = false;
      }
    });
  }

  downloadPdf() {
    if (!this.reportId || this.isDownloading) return;
    this.isDownloading = true;

    this.auditService.downloadAuditPdf(this.reportId).subscribe({
      next: (blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Extract filename format based on date
        const cleanUrl = this.report.website_url.replace(/https?:\/\//, '').replace(/^www\./, '').replace(/\./g, '-').replace(/\//g, '');
        const dateStr = new Date(this.report.created_at).toISOString().split('T')[0];
        a.download = `website-audit-${cleanUrl}-${dateStr}.pdf`;
        
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        this.isDownloading = false;
      },
      error: (err) => {
        console.error('Failed to download PDF', err);
        this.isDownloading = false;
      }
    });
  }

  getScoreColorClass(score: number): string {
    if (score >= 90) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 50) return 'average';
    return 'needs-improvement';
  }

  getPillarTitle(key: string): string {
    const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    return formattedKey;
  }

  getObjectKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }
}
