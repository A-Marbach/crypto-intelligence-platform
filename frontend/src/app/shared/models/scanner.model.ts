
export type ScanStatus =
  | 'candidate'
  | 'watch'
  | 'skipped'
  | 'error';

export interface TimeframeAnalysis {
  trend: string;
  rsi14: string;
}

export interface PullbackAnalysis {
  status: 'pullback_candidate' | 'no_pullback';
  checks: Record<string, boolean>;
  ema_distance_atr: string;
  retracement_atr: string;
  previous_range_low: string;
  previous_range_high: string;
}

export interface MarketReport {
  market: string;
  status: ScanStatus;
  checks_passed: number;
  checks_total: number;
  passed: string[];
  missing: string[];
  reason?: string;
  timeframes?: Record<string, TimeframeAnalysis>;
  pullback?: PullbackAnalysis;
}

export interface ScannerReport {
  generated_at: string;
  summary: {
    scanned: number;
    candidates: number;
    watch: number;
    skipped: number;
    errors: number;
  };
  markets: MarketReport[];
}

export interface CoinPrice {
  market: string;
  price_eur: string | null;
  available: boolean;
}
