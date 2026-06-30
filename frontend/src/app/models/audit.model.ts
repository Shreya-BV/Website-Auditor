export interface ReportRecommendation {
  category: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  current_problem?: string;
  business_impact?: string;
  technical_explanation?: string;
  implementation_steps?: string;
  estimated_time?: string;
  expected_score_improvement?: number;
  difficulty?: string;
  evidence?: string;
}

export interface PerformanceMetrics {
  response_time_ms?: number;
  rendering_time_ms?: number;
  html_download_time_ms?: number;
  playwright_time_ms?: number;
  detection_time_ms?: number;
  total_scan_time_ms?: number;
  rendering_method?: string;
}

export interface TechnologyDetection {
  name: string;
  found: boolean;
  evidence?: string;
  confidence?: number;
}

export interface PillarDetail {
  score: number;
  passed_checks: number;
  failed_checks: number;
  confidence: number;
  business_explanation: string;
  technical_explanation: string;
}

export interface AuditReport {
  id?: string;
  _id?: string;
  audit_id?: string;
  user_id?: string;
  user_name?: string;
  email?: string;
  website_url: string;
  website_title?: string;
  scan_type: string;
  audit_score: number;
  grade?: string;
  benchmark: string;
  target_score: string;
  category_scores: Record<string, number>;
  pillar_details?: Record<string, PillarDetail>;
  recommendations: ReportRecommendation[];
  checks?: any;
  issues_found: number;
  technology_detections?: TechnologyDetection[];
  performance_metrics?: PerformanceMetrics;
  scan_status: string;
  pdf_path?: string;
  pdf_url?: string;
  email_sent: boolean;
  created_at: string;
  updated_at: string;
}
