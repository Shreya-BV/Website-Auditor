import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { AuditReportComponent } from './pages/audit-report/audit-report.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { LeadsComponent } from './pages/leads/leads.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'report/:id', component: AuditReportComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'leads', component: LeadsComponent },
  { path: '**', redirectTo: '' }
];
