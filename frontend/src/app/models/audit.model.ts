export interface Recommendation {
  pillar: string;
  item: string;
  recommendation: string;
  issue?: string;
  reason?: string;
  business_impact?: string;
  how_to_fix?: string;
  estimated_time?: string;
  priority?: string;
  expected_score_increase?: number;
}

export interface CheckResult {
  found: boolean;
  confidence: number;
  method: string;
  evidence?: string;
}

export interface AuditReport {
  id?: string;
  _id?: string;
  url: string;
  overall_score: number;
  grade: string;
  pillar_scores: {
    measurement: number;
    retargeting: number;
    conversion: number;
    trust: number;
    seo_ai: number;
  };
  checks: {
    measurement: {
      google_analytics: CheckResult;
      gtm: CheckResult;
      clarity: CheckResult;
      hotjar: CheckResult;
    };
    retargeting: {
      meta_pixel: CheckResult;
      google_ads: CheckResult;
      linkedin_insight: CheckResult;
      tiktok_pixel: CheckResult;
      pinterest_pixel: CheckResult;
    };
    conversion: {
      contact_form: CheckResult;
      newsletter_form: CheckResult;
      whatsapp: CheckResult;
      messenger: CheckResult;
      live_chat: CheckResult;
      calendly: CheckResult;
      crm: CheckResult;
    };
    trust: {
      https: CheckResult;
      ssl: CheckResult;
      cookies: CheckResult;
      privacy_policy: CheckResult;
      terms: CheckResult;
      contact_page: CheckResult;
      accessibility: CheckResult;
    };
    seo_ai: {
      canonical_url: CheckResult;
      meta_title: CheckResult;
      meta_description: CheckResult;
      sitemap: CheckResult;
      robots: CheckResult;
      schema_markup: CheckResult;
      opengraph: CheckResult;
      twitter_card: CheckResult;
      llms_txt: CheckResult;
      security_headers: CheckResult;
    };
  };
  recommendations: Recommendation[];
  created_at: string;
  updated_at: string;
}
