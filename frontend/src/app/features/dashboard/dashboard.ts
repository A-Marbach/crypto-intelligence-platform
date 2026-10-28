
import {
  Component,
  HostListener,
  inject,
  signal
} from '@angular/core';

import { DatePipe } from '@angular/common';

import {
  catchError,
  finalize,
  forkJoin,
  of
} from 'rxjs';

import { ScannerService } from '../../core/services/scanner';

import {
  CoinPrice,
  MarketReport,
  ScannerReport
} from '../../shared/models/scanner.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard {
  private readonly scannerService = inject(ScannerService);

  readonly report = signal<ScannerReport | null>(null);
  readonly prices = signal<Record<string, CoinPrice>>({});
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly priceError = signal(false);

  readonly selectedMarket = signal<MarketReport | null>(null);

  readonly pullbackChecks = [
    {
      key: 'bullish_4h',
      label: 'Bullisher 4H-Trend'
    },
    {
      key: 'previous_extension',
      label: 'Vorherige Aufwärtsbewegung'
    },
    {
      key: 'retracement',
      label: 'Rücksetzer vorhanden'
    },
    {
      key: 'near_ema20',
      label: 'Kurs nahe EMA20'
    },
    {
      key: 'recovering',
      label: 'Erholung erkennbar'
    }
  ];

  runScan(): void {
    if (this.loading()) {
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.priceError.set(false);

    forkJoin({
      report: this.scannerService.runScan(),
      prices: this.scannerService.getPrices().pipe(
        catchError(() => {
          this.priceError.set(true);
          return of([] as CoinPrice[]);
        })
      )
    })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: ({ report, prices }) => {
          this.report.set(report);

          const priceMap: Record<string, CoinPrice> = {};

          for (const price of prices) {
            priceMap[price.market] = price;
          }

          this.prices.set(priceMap);
          this.closeModal();
        },
        error: () => {
          this.error.set(
            'Scanner fehlgeschlagen. Bitte Backend prüfen.'
          );
        }
      });
  }

  selectMarket(market: MarketReport): void {
    this.selectedMarket.set(market);
  }

  closeModal(): void {
    this.selectedMarket.set(null);
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.selectedMarket()) {
      this.closeModal();
    }
  }

  formatPrice(market: string): string {
    const price = this.prices()[market];

    if (
      !price ||
      !price.available ||
      price.price_eur === null
    ) {
      return '–';
    }

    const value = Number(price.price_eur);

    if (!Number.isFinite(value) || value < 0) {
      return '–';
    }

    let decimals = 2;

    if (value < 1) {
      decimals = 6;
    } else if (value < 100) {
      decimals = 3;
    }

    return new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: 2,
      maximumFractionDigits: decimals
    }).format(value) + ' €';
  }

  tradingViewUrl(market: string): string {
    const symbol = market.replace('-', '');

    return (
      'https://www.tradingview.com/chart/' +
      '?symbol=BITVAVO%3A' +
      encodeURIComponent(symbol)
    );
  }
}
