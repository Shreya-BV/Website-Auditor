import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuditReport } from '../models/audit.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuditService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  scanWebsite(url: string): Observable<AuditReport> {
    return this.http.post<AuditReport>(`${this.apiUrl}/scan`, { url });
  }

  getScanReport(id: string): Observable<AuditReport> {
    return this.http.get<AuditReport>(`${this.apiUrl}/scan/${id}`);
  }

  getAuditReportDetails(id: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/audit/${id}`);
  }

  getAuditHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/audit/history`);
  }

  deleteAudit(id: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/audit/${id}`);
  }

  resendEmail(id: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/audit/send-email/${id}`, {});
  }
}
