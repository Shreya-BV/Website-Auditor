import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuditReport } from '../models/audit.model';

@Injectable({
  providedIn: 'root'
})
export class AuditService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api';

  scanWebsite(url: string): Observable<AuditReport> {
    return this.http.post<AuditReport>(`${this.apiUrl}/scan`, { url });
  }

  getScanReport(id: string): Observable<AuditReport> {
    return this.http.get<AuditReport>(`${this.apiUrl}/scan/${id}`);
  }
}
