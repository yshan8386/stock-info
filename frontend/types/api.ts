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
  briefing_type: string;
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
  summary?: string;
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

export type PositionDashboard = {
  mode: "read_only" | "paper" | "live";
  trading_enabled: boolean;
  as_of: string;
  settings: TradingSettings;
  batch: {
    is_running: boolean;
    last_run_at: string | null;
    last_run_status: string | null;
    captured_signal_count: number;
    message: string;
  };
  account: {
    total_equity: number;
    cash: number;
    invested_amount: number;
    day_pnl: number;
    day_pnl_pct: number;
    total_pnl: number;
    total_pnl_pct: number;
    buying_power: number;
  };
  risk_statuses: {
    name: string;
    status: "ok" | "watch" | "blocked";
    message: string;
  }[];
  strategies: {
    strategy_id: string;
    strategy_label: string;
    status: "active" | "watching" | "paused";
    allocated_capital: number;
    deployed_capital: number;
    open_positions: number;
    max_positions: number;
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
    next_action: string;
  }[];
  positions: {
    symbol: string;
    name: string;
    strategy_id: string;
    quantity: number;
    average_price: number;
    current_price: number;
    market_value: number;
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
    stop_loss: number;
    take_profit: number;
    entry_reason: string;
  }[];
  watchlist: {
    symbol: string;
    name: string;
    strategy_id: string;
    signal: string;
    current_price: number;
    trigger_price: number;
    risk_note: string;
  }[];
  recent_signals: TradingSignal[];
};

export type TradingSettings = {
  batch_enabled: boolean;
  live_trading_enabled: boolean;
  selected_strategy_ids: string[];
  batch_interval_seconds: number;
};

export type TradingSignal = {
  id: number;
  strategy_id: string;
  symbol: string;
  name: string;
  side: string;
  signal: string;
  current_price: number;
  trigger_price: number;
  confidence: number;
  execution_mode: string;
  status: string;
  risk_note: string;
  created_at: string;
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

export type OhlcvCandle = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type BacktestConfig = {
  initial_capital?: number;
  position_size_pct?: number;
  lookback_period?: number;
  swing_window?: number;
  slope_period?: number;
  volume_period?: number;
  min_volume_ratio?: number;
  min_slope_atr?: number;
  level_tolerance_pct?: number;
  breakout_buffer_pct?: number;
  stop_loss_buffer_pct?: number;
  risk_reward_ratio?: number;
  commission_rate?: number;
  tax_rate?: number;
  slippage_pct?: number;
};

export type PriceLevel = {
  price: number;
  kind: "support" | "resistance";
  strength: number;
  touches: number;
  last_touched_at: string | null;
};

export type BacktestTrade = {
  entry_at: string;
  entry_price: number;
  quantity: number;
  reason: string;
  entry_rsi: number | null;
  entry_volume_ratio: number | null;
  stop_loss: number;
  take_profit: number;
  exit_at: string | null;
  exit_price: number | null;
  exit_reason: string | null;
  exit_rsi: number | null;
  exit_volume_ratio: number | null;
  pnl: number | null;
  pnl_pct: number | null;
};

export type EquityPoint = {
  timestamp: string;
  equity: number;
  cash: number;
  position_value: number;
  close: number;
};

export type BenchmarkPoint = {
  timestamp: string;
  close: number;
};

export type BacktestResult = {
  symbol: string;
  symbol_name: string | null;
  avg_trade_amount: number | null;
  metrics: {
    initial_capital: number;
    final_capital: number;
    total_return_pct: number;
    max_drawdown_pct: number;
    trade_count: number;
    win_rate_pct: number;
    profit_factor: number;
    sharpe_ratio: number;
  };
  supports: PriceLevel[];
  resistances: PriceLevel[];
  trades: BacktestTrade[];
  equity_curve: EquityPoint[];
  notes: string[];
};

export type StrategyInfo = {
  id: string;
  label: string;
  description: string;
};

export type StrategyComparisonSummary = {
  strategy_id: string;
  strategy_label: string;
  initial_capital: number;
  final_capital: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  trade_count: number;
  win_rate_pct: number;
  sharpe_ratio: number;
};

export type StrategyBacktestRun = {
  strategy: StrategyInfo;
  summary: StrategyComparisonSummary;
  results: BacktestResult[];
  benchmark_curve: BenchmarkPoint[];
};

export type StockSelectionItem = {
  symbol: string;
  name: string;
  avg_trade_amount: number;
  current_price: number;
  market_cap: number | null;
  allocated_budget: number | null;
  max_buyable_quantity: number | null;
  score: number;
  reason: string;
};

export type AutoBacktestResult = {
  request: {
    start_date: string;
    end_date: string;
    initial_capital: number;
    min_avg_trade_amount: number;
    max_symbols: number;
    max_positions: number;
    strategy_ids: string[];
  };
  selected: StockSelectionItem[];
  strategy_runs: StrategyBacktestRun[];
  results: BacktestResult[];
  notes: string[];
};

export type StockSearchItem = {
  symbol: string;
  name: string;
  current_price: number;
};

export type StockDetail = {
  symbol: string;
  name: string;
  market_name: string | null;
  sector_name: string | null;
  current_price: number | null;
  previous_close: number | null;
  change_amount: number | null;
  change_rate: number | null;
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  volume: number | null;
  trade_amount: number | null;
  market_cap: number | null;
  shares_outstanding: number | null;
  week52_high: number | null;
  week52_low: number | null;
  per: number | null;
  pbr: number | null;
  eps: number | null;
  bps: number | null;
  selection_date: string | null;
  candle_date: string | null;
  selection_open_price: number | null;
  selection_high_price: number | null;
  selection_low_price: number | null;
  selection_close_price: number | null;
  selection_volume: number | null;
  chart_candles: {
    candle_date: string;
    open_price: number;
    high_price: number;
    low_price: number;
    close_price: number;
    volume: number;
  }[];
};

export type StockSelectionResult = {
  selected: StockSelectionItem[];
  notes: string[];
};

export type SelectedSymbol = {
  symbol: string;
  name: string;
};

export type StrategyRunsResult = {
  strategy_runs: StrategyBacktestRun[];
  notes: string[];
};

export type StockSelectionDateResult = {
  selection_date: string;
  selected: StockSelectionItem[];
};

export type StockSelectionRangeResult = {
  results: StockSelectionDateResult[];
  notes: string[];
};

export type KisOhlcvEndpointInfo = {
  market: string;
  timeframe: string;
  endpoint: string;
  tr_id: string;
  max_rows_per_call: number;
  output: string;
  fields: Record<string, string>;
};
