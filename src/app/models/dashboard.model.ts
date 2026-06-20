import { Lead } from './lead.model';
import { VisitorLog } from './visitor.model';

export interface DailyCount {
  date: string;
  count: number;
}

export interface DashboardStats {
  total_visitors: number;
  total_scans: number;
  total_leads: number;
  recent_leads: Lead[];
  recent_visitors: VisitorLog[];
  scans_by_day?: DailyCount[];
  leads_by_day?: DailyCount[];
}
