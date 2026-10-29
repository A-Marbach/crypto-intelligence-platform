
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

interface Trade {
  executed_at: string;
  side: 'buy' | 'sell';
  symbol: string;
  price_eur: string;
  quantity: string;
  gross_eur: string;
  fees_eur: string;
  total_eur: string;
  executions: number;
}

interface TradesResponse {
  count: number;
  trades: Trade[];
  history_complete: boolean;
}

@Component({
  selector: 'app-trade-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './trade-history.html',
  styleUrl: './trade-history.scss',
})
export class TradeHistory implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);

  readonly history = signal<TradesResponse | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    timer(0, 30_000)
      .pipe(
        exhaustMap(() =>
          this.http.get<TradesResponse>(
            'http://127.0.0.1:8001/api/v1/portfolio/trades'
          ).pipe(
            tap((result) => {
              this.history.set(result);
              this.loading.set(false);
              this.error.set(null);
            }),
            catchError(() => {
              this.error.set(
                'Trade-Historie konnte nicht geladen werden.'
              );
              this.loading.set(false);
              return EMPTY;
            })
          )
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe();
  }
}
