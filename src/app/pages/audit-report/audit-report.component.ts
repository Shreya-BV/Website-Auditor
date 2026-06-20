import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuditService } from '../../services/audit.service';
import { LeadService } from '../../services/lead.service';
import { AuditReport } from '../../models/audit.model';

@Component({
  selector: 'app-audit-report',
  imports: [CommonModule, FormsModule],
  templateUrl: './audit-report.component.html',
  styleUrl: './audit-report.component.scss'
})
export class AuditReportComponent implements OnInit {
  reportId = '';
  report: AuditReport | null = null;
  isLoading = true;
  errorMessage = '';

  // Lead capture form
  leadName = '';
  leadEmail = '';
  isSubmittingLead = false;
  leadSubmitted = false;
  leadError = '';

  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private auditService = inject(AuditService);
  private leadService = inject(LeadService);

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
    this.auditService.getScanReport(id).subscribe({
      next: (data) => {
        this.report = data;
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Failed to load the scan report. It may have expired or does not exist.';
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

  submitLead() {
    if (!this.leadName.trim() || !this.leadEmail.trim()) {
      this.leadError = 'Please fill out both Name and Email fields.';
      return;
    }

    if (!this.report) return;

    this.isSubmittingLead = true;
    this.leadError = '';

    this.leadService.submitLead(
      this.leadName,
      this.leadEmail,
      this.report.url,
      this.report.overall_score
    ).subscribe({
      next: () => {
        this.isSubmittingLead = false;
        this.leadSubmitted = true;
      },
      error: (err) => {
        this.isSubmittingLead = false;
        this.leadError = err.error?.detail || 'Failed to submit details. Please try again.';
      }
    });
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

  // Helper to format keys like google_analytics to Google Analytics
  formatCheckName(key: string): string {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
      .replace('Gtm', 'Google Tag Manager')
      .replace('Ssl', 'SSL Certificate')
      .replace('Crm', 'CRM Integration')
      .replace('Https', 'HTTPS Protocol')
      .replace('Seo', 'SEO')
      .replace('Ai', 'AI')
      .replace('Txt', 'txt')
      .replace('Opengraph', 'OpenGraph Tags')
      .replace('Twitter Card', 'Twitter Cards')
      .replace('Llms', 'llms');
  }

  getPillarScore(pillarKey: string): number {
    if (!this.report) return 0;
    const scores = this.report.pillar_scores as any;
    return scores[pillarKey] || 0;
  }

  getPillarChecks(pillarKey: string): any {
    if (!this.report) return {};
    const checks = this.report.checks as any;
    return checks[pillarKey] || {};
  }

  // Get keys of an object
  getObjectKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }
}
