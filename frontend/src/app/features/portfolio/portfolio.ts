
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  Component,
  DestroyRef,
  OnInit,
  inject,
  signal
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, timer } from 'rxjs';
import { catchError, exhaustMap, tap } from 'rxjs/operators';

import { TradeHistory } from '../trade-history/trade-history';

interface PortfolioAsset {
  symbol: string;
  available: string;
  in_order: string;
  total: string;
  price_eur: string | null;
  value_eur: string | null;
}

interface PortfolioSummary {
  total_value_eur: string | null;
  known_value_eur: string;
  eur_available: string;
  valuation_complete: boolean;
  missing_prices: string[];
  assets: PortfolioAsset[];
}

interface PnlPosition {
  symbol: string;
  quantity: string;
  cost_basis_eur: string;
  average_cost_eur: string | null;
  market_price_eur: string | null;
  market_value_eur: string | null;
  unrealized_pnl_eur: string | null;
  realized_pnl_eur: string;
  buy_executions: number;
  sell_executions: number;
}

interface PnlResponse {
  cost_basis_method: string;
  realized_pnl_eur: string;
  unrealized_pnl_eur: string | null;
  valuation_complete: boolean;
  positions: PnlPosition[];
  rebates_included: boolean;
}

@Component({
  selector: 'app-portfolio',
  standalone: true,
  imports: [CommonModule, TradeHistory],
  templateUrl: './portfolio.html',
  styleUrl: './portfolio.scss',
})
export class PortfolioComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);

  readonly portfolio = signal<PortfolioSummary | null>(null);
  readonly pnl = signal<PnlResponse | null>(null);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly pnlError = signal<string | null>(null);
  readonly lastUpdated = signal<Date | null>(null);

  ngOnInit(): void {
    // Bestehendes Portfolio weiterhin alle 30 Sekunden laden.
    timer(0, 30_000)
      .pipe(
        exhaustMap(() =>
          this.http.get<PortfolioSummary>(
            'http://127.0.0.1:8001/api/v1/portfolio/summary'
          ).pipe(
            tap((data) => {
              this.portfolio.set(data);
              this.lastUpdated.set(new Date());
              this.error.set(null);
              this.loading.set(false);
            }),
            catchError(() => {
              this.error.set(
                'Portfolio konnte nicht aktualisiert werden.'
              );
              this.loading.set(false);
              return EMPTY;
            })
          )
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe();

    // Neue Gewinn- und Verlustanalyse.
    timer(0, 30_000)
      .pipe(
        exhaustMap(() =>
          this.http.get<PnlResponse>(
            'http://127.0.0.1:8001/api/v1/portfolio/pnl'
          ).pipe(
            tap((data) => {
              this.pnl.set(data);
              this.pnlError.set(null);
            }),
            catchError(() => {
              this.pnlError.set(
                'Gewinn- und Verlustanalyse nicht verfügbar.'
              );
              this.pnl.set(null);
              return EMPTY;
            })
          )
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe();
  }
}
