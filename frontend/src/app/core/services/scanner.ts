
import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  CoinPrice,
  ScannerReport
} from '../../shared/models/scanner.model';

@Injectable({
  providedIn: 'root'
})
export class ScannerService {
  private readonly http = inject(HttpClient);

  runScan(): Observable<ScannerReport> {
    return this.http.get<ScannerReport>(
      '/api/v1/scanner/report/summary'
    );
  }

  getPrices(): Observable<CoinPrice[]> {
    return this.http.get<CoinPrice[]>(
      '/api/v1/coins/prices'
    );
  }
}
