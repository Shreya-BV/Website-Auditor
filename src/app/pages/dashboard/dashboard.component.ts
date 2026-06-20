import { Component, OnInit, AfterViewChecked, ViewChild, ElementRef, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { DashboardService } from '../../services/dashboard.service';
import { DashboardStats } from '../../models/dashboard.model';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit, OnDestroy, AfterViewChecked {
  stats: DashboardStats | null = null;
  isLoading = true;
  errorMessage = '';
  chart: Chart | null = null;

  @ViewChild('analyticsChart') analyticsChartCanvas!: ElementRef<HTMLCanvasElement>;

  private dashboardService = inject(DashboardService);

  ngOnInit() {
    this.loadStats();
  }

  ngOnDestroy() {
    if (this.chart) {
      this.chart.destroy();
    }
  }

  ngAfterViewChecked() {
    if (this.stats && !this.isLoading && !this.chart && this.analyticsChartCanvas) {
      this.initChart();
    }
  }

  loadStats() {
    this.isLoading = true;
    this.errorMessage = '';
    this.dashboardService.getStats().subscribe({
      next: (data) => {
        this.stats = data;
        this.isLoading = false;
        // Chart will be initialized in ngAfterViewChecked once the canvas is rendered
      },
      error: (err) => {
        this.errorMessage = 'Failed to load dashboard statistics. Please ensure the backend is running.';
        this.isLoading = false;
        console.error(err);
      }
    });
  }

  get conversionRate(): number {
    if (!this.stats || this.stats.total_scans === 0) return 0;
    const rate = (this.stats.total_leads / this.stats.total_scans) * 100;
    return Math.round(rate * 10) / 10;
  }

  initChart() {
    if (!this.analyticsChartCanvas || !this.stats) return;

    const ctx = this.analyticsChartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    // Destroy existing chart if it exists
    if (this.chart) {
      this.chart.destroy();
    }

    // Prepare chart data
    const scanData = this.stats.scans_by_day || [];
    const leadData = this.stats.leads_by_day || [];

    // Extract unique sorted dates for labels
    const allDates = Array.from(new Set([
      ...scanData.map(d => d.date),
      ...leadData.map(d => d.date)
    ])).sort();

    // Fill missing values with 0
    const scanCounts = allDates.map(date => {
      const found = scanData.find(d => d.date === date);
      return found ? found.count : 0;
    });

    const leadCounts = allDates.map(date => {
      const found = leadData.find(d => d.date === date);
      return found ? found.count : 0;
    });

    // Provide friendly date format labels
    const formattedLabels = allDates.map(dateStr => {
      const [year, month, day] = dateStr.split('-');
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    });

    // Fallback if no data is present
    const labels = formattedLabels.length > 0 ? formattedLabels : ['No Data'];
    const finalScans = scanCounts.length > 0 ? scanCounts : [0];
    const finalLeads = leadCounts.length > 0 ? leadCounts : [0];

    // Determine font color based on theme (always light now)
    const textColor = '#64748B';
    const gridColor = '#E2E8F0';

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Websites Scanned',
            data: finalScans,
            borderColor: '#3B82F6', // Blue
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.3,
            fill: true,
            borderWidth: 2,
            pointBackgroundColor: '#3B82F6',
          },
          {
            label: 'Leads Captured',
            data: finalLeads,
            borderColor: '#10B981', // Green
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.3,
            fill: true,
            borderWidth: 2,
            pointBackgroundColor: '#10B981',
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: textColor,
              font: {
                family: 'Plus Jakarta Sans',
                weight: 500
              }
            }
          }
        },
        scales: {
          x: {
            grid: {
              color: gridColor
            },
            ticks: {
              color: textColor
            }
          },
          y: {
            grid: {
              color: gridColor
            },
            ticks: {
              color: textColor,
              precision: 0
            },
            beginAtZero: true
          }
        }
      }
    });
  }

  // Helper browser icon resolver
  getBrowserIcon(browser: string): string {
    switch(browser.toLowerCase()) {
      case 'chrome': return '🌐';
      case 'firefox': return '🦊';
      case 'safari': return '🧭';
      case 'edge': return '🌐';
      default: return '💻';
    }
  }
}
