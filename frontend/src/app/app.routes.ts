
import { Routes } from '@angular/router';

import { Dashboard } from './features/dashboard/dashboard';
import { PortfolioComponent } from './features/portfolio/portfolio';

export const routes: Routes = [
  {
    path: '',
    component: PortfolioComponent,
    title: 'Mein Trading Dashboard',
  },
  {
    path: 'scanner',
    component: Dashboard,
    title: 'Crypto Market Scanner',
  },
  {
    path: '**',
    redirectTo: '',
  },
];
