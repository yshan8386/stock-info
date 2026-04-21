export type User = {
  id: number;
  username: string;
  display_name: string;
  email: string;
  created_at: string;
};

export type BriefingArchiveItem = {
  id: number;
  briefing_date: string;
  title: string | null;
  one_liner: string | null;
  generated_at: string;
};

export type BriefingHighlight = {
  news_id: number;
  title: string;
  title_ko?: string;
  url: string;
  source: string;
  reason: string;
};

export type BriefingSection = {
  label: string;
  summary: string;
  highlights: BriefingHighlight[];
};

export type Briefing = BriefingArchiveItem & {
  briefing_type: string;
  content_markdown: string;
  content_sections: Record<string, BriefingSection> | null;
  keywords: string[] | null;
  source_article_count: number | null;
  model_used: string | null;
};

export type DashboardSummary = {
  today_briefing: BriefingArchiveItem | null;
  backtest: { status: string };
  position: { status: string };
  glossary: {
    total_terms: number;
    recent_added: string[];
  };
};

export type GlossaryCategory = {
  id: number;
  name: string;
  slug: string;
  icon: string | null;
  sort_order: number;
};

export type GlossaryTerm = {
  id: number;
  category_id: number;
  term_ko: string;
  term_en: string | null;
  short_desc: string;
  detail_markdown: string | null;
  formula: string | null;
  example: string | null;
  related_term_ids: number[] | null;
  category?: GlossaryCategory | null;
};

export type GlossaryGroup = {
  category: GlossaryCategory;
  terms: GlossaryTerm[];
};

export type Feed = {
  id: number;
  name: string;
  url: string;
  category: string;
  language: string;
  is_active: boolean;
  last_fetched_at: string | null;
  last_fetched_status: string | null;
  last_error: string | null;
  fetch_interval_minutes: number;
};
