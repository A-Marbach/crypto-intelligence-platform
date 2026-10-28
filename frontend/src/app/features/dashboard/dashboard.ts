
import {
  Component,
  HostListener,
  OnDestroy,
  OnInit,
  inject,
  signal
} from '@angular/core';

import { DatePipe } from '@angular/common';

import {
  catchError,
  finalize,
  forkJoin,
  interval,
  of,
  Subscription
} from 'rxjs';

import { ScannerService } from '../../core/services/scanner';

import {
  CoinPrice,
  MarketReport,
  ScannerReport
} from '../../shared/models/scanner.model';

const SCAN_INTERVAL_MS = 15 * 60 * 1000;

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard implements OnInit, OnDestroy {
  private readonly scannerService = inject(ScannerService);

  private autoScanSubscription?: Subscription;
  private scanSubscription?: Subscription;

  readonly report = signal<ScannerReport | null>(null);
  readonly prices = signal<Record<string, CoinPrice>>({});

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly priceError = signal(false);

  readonly autoScanEnabled = signal(true);
  readonly nextScanAt = signal<Date | null>(null);

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

  // Start scanner when dashboard opens
  ngOnInit(): void {
    this.runScan();
    this.startAutoScanTimer();
  }

  // Clean up subscriptions
  ngOnDestroy(): void {
    this.autoScanSubscription?.unsubscribe();
    this.scanSubscription?.unsubscribe();
  }

  // Automatic scanner every 15 minutes
  private startAutoScanTimer(): void {
    this.autoScanSubscription?.unsubscribe();

    if (!this.autoScanEnabled()) {
      this.nextScanAt.set(null);
      return;
    }

    this.nextScanAt.set(
      new Date(Date.now() + SCAN_INTERVAL_MS)
    );

    this.autoScanSubscription = interval(
      SCAN_INTERVAL_MS
    ).subscribe(() => {
      if (this.autoScanEnabled()) {
        this.runScan();

        this.nextScanAt.set(
          new Date(Date.now() + SCAN_INTERVAL_MS)
        );
      }
    });
  }

  // Manual or automatic scan
  runScan(): void {
    if (this.loading()) {
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.priceError.set(false);

    this.scanSubscription = forkJoin({
      report: this.scannerService.runScan(),
      prices: this.scannerService.getPrices().pipe(
        catchError(() => {
          this.priceError.set(true);
          return of([] as CoinPrice[]);
        })
      )
    })
      .pipe(
        finalize(() => {
          this.loading.set(false);
        })
      )
      .subscribe({
        next: ({ report, prices }) => {
          this.report.set(report);

          const priceMap: Record<string, CoinPrice> = {};

          for (const price of prices) {
            priceMap[price.market] = price;
          }

          this.prices.set(priceMap);

          // Refresh the selected coin without closing the modal.
          const selected = this.selectedMarket();

          if (selected) {
            const updatedMarket = report.markets.find(
              market => market.market === selected.market
            );

            this.selectedMarket.set(updatedMarket ?? null);
          }
        },

        error: () => {
          this.error.set(
            'Scanner fehlgeschlagen. Bitte FastAPI-Backend prüfen.'
          );
        }
      });
  }

  // Enable or disable automatic scanning
  toggleAutoScan(): void {
    const enabled = !this.autoScanEnabled();

    this.autoScanEnabled.set(enabled);

    if (enabled) {
      this.runScan();
      this.startAutoScanTimer();
    } else {
      this.autoScanSubscription?.unsubscribe();
      this.autoScanSubscription = undefined;
      this.nextScanAt.set(null);
    }
  }

  // Open detail modal
  selectMarket(market: MarketReport): void {
    this.selectedMarket.set(market);
  }

  // Close detail modal
  closeModal(): void {
    this.selectedMarket.set(null);
  }

  // Close modal with Escape
  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.selectedMarket()) {
      this.closeModal();
    }
  }

  // Format prices for the German locale
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

  // TradingView chart for each Bitvavo market
  tradingViewUrl(market: string): string {
    const symbol = market.replace('-', '');

    return (
      'https://www.tradingview.com/chart/' +
      '?symbol=BITVAVO%3A' +
      encodeURIComponent(symbol)
    );
  }
}
