import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DashboardService } from '../../services/dashboard.service';
import { Lead } from '../../models/lead.model';

@Component({
  selector: 'app-leads',
  imports: [CommonModule, FormsModule],
  templateUrl: './leads.component.html',
  styleUrl: './leads.component.scss'
})
export class LeadsComponent implements OnInit {
  leads: Lead[] = [];
  filteredLeads: Lead[] = [];
  isLoading = true;
  errorMessage = '';
  searchTerm = '';
  leadToDelete: Lead | null = null;

  private dashboardService = inject(DashboardService);
  private snackBar = inject(MatSnackBar);

  ngOnInit() {
    this.loadLeads();
  }

  loadLeads() {
    this.isLoading = true;
    this.errorMessage = '';
    this.dashboardService.getLeads().subscribe({
      next: (data) => {
        this.leads = data;
        this.applyFilter();
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = 'Failed to load captured leads list. Please ensure the backend is online.';
        this.isLoading = false;
        console.error(err);
      }
    });
  }

  applyFilter() {
    const term = this.searchTerm.trim().toLowerCase();
    if (!term) {
      this.filteredLeads = [...this.leads];
      return;
    }

    this.filteredLeads = this.leads.filter(lead => 
      lead.name.toLowerCase().includes(term) ||
      lead.email.toLowerCase().includes(term) ||
      lead.website_url.toLowerCase().includes(term)
    );
  }

  exportToCsv() {
    if (this.filteredLeads.length === 0) return;

    const headers = ['Name', 'Email', 'Website URL', 'Audit Score', 'Registered At'];
    const rows = this.filteredLeads.map(lead => [
      lead.name,
      lead.email,
      lead.website_url,
      lead.audit_score.toString(),
      lead.created_at ? this.formatDateIST(lead.created_at) : 'Not Available'
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(e => e.map(val => `"${val.replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `leads_export_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  formatDateIST(dateString: string): string {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Not Available';
    
    const options: Intl.DateTimeFormatOptions = {
      timeZone: 'Asia/Kolkata',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    };
    
    const formatter = new Intl.DateTimeFormat('en-US', options);
    return formatter.format(date) + ' IST';
  }

  confirmDeleteModal(lead: Lead) {
    this.leadToDelete = lead;
  }

  cancelDelete() {
    this.leadToDelete = null;
  }

  confirmDelete() {
    if (!this.leadToDelete) return;

    const leadId = this.leadToDelete._id || this.leadToDelete.id;
    if (!leadId) {
      this.cancelDelete();
      return;
    }

    this.dashboardService.deleteLead(leadId).subscribe({
      next: (response: any) => {
        this.leads = this.leads.filter(l => (l._id || l.id) !== leadId);
        this.applyFilter();
        this.leadToDelete = null;
        
        // Ensure we are using the backend message or default
        const message = response?.message || '✓ Lead deleted successfully';
        this.snackBar.open(message, '', {
          duration: 3000,
          horizontalPosition: 'right',
          verticalPosition: 'top',
          panelClass: ['success-snackbar']
        });
      },
      error: (err) => {
        console.error(err);
        this.snackBar.open('✗ Failed to delete lead. Please try again.', '', {
          duration: 5000,
          horizontalPosition: 'right',
          verticalPosition: 'top',
          panelClass: ['error-snackbar']
        });
        this.leadToDelete = null;
      }
    });
  }
}
