export interface Recommendation {
  pillar: string;
  item: string;
  recommendation: string;
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
      google_analytics: boolean;
      gtm: boolean;
      clarity: boolean;
      hotjar: boolean;
    };
    retargeting: {
      meta_pixel: boolean;
      google_ads: boolean;
      linkedin_insight: boolean;
    };
    conversion: {
      contact_form: boolean;
      whatsapp: boolean;
      live_chat: boolean;
      crm: boolean;
      lead_popup: boolean;
    };
    trust: {
      https: boolean;
      ssl: boolean;
      privacy_policy: boolean;
      terms: boolean;
      contact_page: boolean;
    };
    seo_ai: {
      meta_title: boolean;
      meta_description: boolean;
      sitemap: boolean;
      robots: boolean;
      schema_markup: boolean;
      opengraph: boolean;
      twitter_card: boolean;
      llms_txt: boolean;
    };
  };
  recommendations: Recommendation[];
  created_at: string;
  updated_at: string;
}
