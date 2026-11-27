/*
 * Collected competitor price data.
 *
 * This module contains no private or locally generated seed file. Its arrays
 * remain in the mock API so a fresh clone can build without external data.
 * Replace these values with real API data in a future backend integration.
 */

export interface CollectedCompetitorPrice {
  id: string;
  marketplaceCode: 'TIKTOK_SHOP';
  categoryId: string;
  categoryName: string;
  externalProductId: string;
  productTitle: string;
  url: string;
  sellerId: string;
  sellerName: string;
  brand: string | null;
  listedPrice: number | null;
  effectivePrice: number;
  currency: 'VND';
  discountPercent: number | null;
  isPromotional: boolean;
  rating: number | null;
  reviewCount: number;
  soldCount: number;
  skuCount: number;
  isOutlier: boolean;
  observedAt: string;
  sourceType: 'API';
  sourceName: string;
  confidence: number;
}

export interface CollectedMeta {
  marketplaceCode: string;
  market: string;
  collectedAt: string;
  source: string;
  categoryCounts: Record<string, number>;
  total: number;
  note: string;
}

export const COLLECTED_COMPETITOR_META: CollectedMeta = {
  marketplaceCode: 'TIKTOK_SHOP',
  market: 'vn',
  collectedAt: '',
  source: '',
  categoryCounts: {},
  total: 0,
  note: 'Demo empty state',
};

export const COLLECTED_COMPETITOR_PRICES: CollectedCompetitorPrice[] = [];

/** Records safe to use as a pricing signal (fresh, not bait). */
export function usableCollectedPrices(): CollectedCompetitorPrice[] {
  return COLLECTED_COMPETITOR_PRICES.filter((r) => !r.isOutlier && r.effectivePrice > 0);
}