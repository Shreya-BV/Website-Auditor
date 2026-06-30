import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { AuditReportComponent } from './pages/audit-report/audit-report.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { LeadsComponent } from './pages/leads/leads.component';
import { AuditHistoryComponent } from './pages/audit-history/audit-history.component';
import { AuditReportDetailsComponent } from './pages/audit-report-details/audit-report-details.component';
import { LoginComponent } from './pages/login/login.component';
import { RegisterComponent } from './pages/register/register.component';
import { ForgotPasswordComponent } from './pages/forgot-password/forgot-password.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'forgot-password', component: ForgotPasswordComponent },
  { path: '', component: HomeComponent, canActivate: [authGuard] },
  { path: 'report/:id', component: AuditReportComponent, canActivate: [authGuard] },
  { path: 'audit-report/:id', component: AuditReportDetailsComponent, canActivate: [authGuard] },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'leads', component: LeadsComponent, canActivate: [authGuard] },
  { path: 'history', component: AuditHistoryComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: '' }
];
