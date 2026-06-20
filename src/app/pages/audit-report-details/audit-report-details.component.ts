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

  getScoreColorClass(score: number): string {
    if (score >= 90) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 50) return 'average';
    return 'needs-improvement';
  }

  getPillarTitle(key: string): string {
    switch(key) {
      case 'measurement': return 'Measurement & Analytics';
      case 'retargeting': return 'Retargeting Tags';
      case 'conversion': return 'Conversion & CRM';
      case 'trust': return 'Trust & Security';
      case 'seo_ai': return 'SEO & AI Search';
      default: return key;
    }
  }

  getObjectKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }
}
