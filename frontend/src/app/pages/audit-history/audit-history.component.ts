import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuditService } from '../../services/audit.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-audit-history',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './audit-history.component.html',
  styleUrl: './audit-history.component.scss'
})
export class AuditHistoryComponent implements OnInit {
  reports: any[] = [];
  isLoading = true;
  errorMessage = '';
  downloadingReportId: string | null = null;

  private auditService = inject(AuditService);

  ngOnInit() {
    this.loadHistory();
  }

  loadHistory() {
    this.isLoading = true;
    this.errorMessage = '';
    this.auditService.getAuditHistory().subscribe({
      next: (data) => {
        this.reports = data;
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = 'Failed to load audit history. ' + (err.error?.detail || '');
        this.isLoading = false;
      }
    });
  }

  downloadPdf(reportId: string, report: any, event: Event) {
    event.stopPropagation();
    if (this.downloadingReportId) return;
    this.downloadingReportId = reportId;

    this.auditService.downloadAuditPdf(reportId).subscribe({
      next: (blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        const cleanUrl = report.website_url.replace(/https?:\/\//, '').replace(/^www\./, '').replace(/\./g, '-').replace(/\//g, '');
        const dateStr = new Date(report.created_at).toISOString().split('T')[0];
        a.download = `website-audit-${cleanUrl}-${dateStr}.pdf`;
        
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        this.downloadingReportId = null;
      },
      error: (err) => {
        console.error('Failed to download PDF', err);
        alert('Failed to download PDF report. It may not exist.');
        this.downloadingReportId = null;
      }
    });
  }

  deleteReport(reportId: string, event: Event) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this report? This action cannot be undone.')) return;
    
    this.auditService.deleteAudit(reportId).subscribe({
      next: () => {
        this.reports = this.reports.filter(r => (r._id || r.id) !== reportId);
      },
      error: (err) => {
        alert('Failed to delete report: ' + (err.error?.detail || 'Unknown error'));
      }
    });
  }

  getScoreColorClass(score: number): string {
    if (score >= 90) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 50) return 'average';
    return 'needs-improvement';
  }
}
