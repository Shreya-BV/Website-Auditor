import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Lead } from '../models/lead.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class LeadService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  submitLead(name: string, email: string, websiteUrl: string, auditScore: number): Observable<Lead> {
    return this.http.post<Lead>(`${this.apiUrl}/lead`, {
      name,
      email,
      website_url: websiteUrl,
      audit_score: auditScore
    });
  }
}
