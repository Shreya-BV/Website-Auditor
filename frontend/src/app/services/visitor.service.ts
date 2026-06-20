import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { VisitorLog } from '../models/visitor.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class VisitorService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  trackVisitor(page: string): Observable<VisitorLog> {
    const userAgent = navigator.userAgent;
    const referrer = document.referrer || 'Direct';
    
    return this.http.post<VisitorLog>(`${this.apiUrl}/visitor`, {
      browser: this.getBrowser(userAgent),
      device: this.getDevice(userAgent),
      referrer: referrer,
      page_visited: page
    });
  }

  private getBrowser(ua: string): string {
    if (ua.includes('Firefox')) return 'Firefox';
    if (ua.includes('Chrome') && !ua.includes('Chromium')) return 'Chrome';
    if (ua.includes('Safari') && !ua.includes('Chrome')) return 'Safari';
    if (ua.includes('Edge')) return 'Edge';
    return 'Other';
  }

  private getDevice(ua: string): string {
    if (/Mobi|Android|iPhone/i.test(ua)) return 'Mobile';
    if (/Tablet|iPad/i.test(ua)) return 'Tablet';
    return 'Desktop';
  }
}
