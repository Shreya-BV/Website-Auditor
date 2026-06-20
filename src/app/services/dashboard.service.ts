import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { DashboardStats } from '../models/dashboard.model';
import { Lead } from '../models/lead.model';
import { VisitorLog } from '../models/visitor.model';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api';

  getStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.apiUrl}/dashboard/stats`);
  }

  getLeads(): Observable<Lead[]> {
    return this.http.get<Lead[]>(`${this.apiUrl}/dashboard/leads`);
  }

  getVisitors(): Observable<VisitorLog[]> {
    return this.http.get<VisitorLog[]>(`${this.apiUrl}/dashboard/visitors`);
  }

  deleteLead(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/lead/${id}`);
  }
}
