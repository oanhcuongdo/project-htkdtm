/*
 * Mock API layer — DEMO only.
 * Proxy shape matches API_SPEC.md envelopes so swapping to FastAPI later is a
 * single-file change. Never import `mocks/data` from components.
 *
 * The pricing run below is a deterministic rule-based implementation of
 * AI_PRICING §5/§8 (floor, anchor, clamp, round) so the demo shows the same
 * numbers the backend will produce. It is still DEMO data, not live pricing.
 */
import type {
  AuditLog,
  Channel,
  ChannelFee,
  ChannelListing,
  Competitor,
  CompetitorPrice,
  DashboardSummary,
  ExecutionRun,
  Explanation,
  InventoryBalance,
  Paged,
  PricingJob,
  PricingRule,
  PricingSchedule,
  Product,
  Recommendation,
  Supplier,
  User,
} from '@/types/domain';
import {
  AUDIT_LOGS,
  CHANNEL_FEES,
  CHANNEL_LISTINGS,
  CHANNELS,
  COMPETITORS,
  COMPETITOR_PRICES,
  DASHBOARD,
  DEMO_USERS,
  EXECUTIONS,
  INVENTORY,
  PRICING_JOBS,
  PRICING_RULES,
  PRICING_SCHEDULES,
  PRODUCTS,
  RECOMMENDATIONS,
  SUPPLIERS,
} from './data';
import {
  COLLECTED_COMPETITOR_META,
  COLLECTED_COMPETITOR_PRICES,
  type CollectedCompetitorPrice,
  type CollectedMeta,
} from './collected';

const clone = <T>(v: T): T => structuredClone(v);
const wait = (ms = 320) => new Promise((r) => setTimeout(r, ms));
const EMPTY_DEMO = import.meta.env.VITE_EMPTY_DEMO !== 'false';

/** BUSINESS_RULES §5 — retry is bounded, default 3. */
export const MAX_ATTEMPTS = 3;
/** BUSINESS_RULES §6 — no automatic change larger than 20% without review. */
export const MAX_PRICE_CHANGE_PCT = 0.2;
const COMPETITOR_MAX_AGE_HOURS = 24;
const PRICE_INCREMENT = 1000;

let recommendations = EMPTY_DEMO ? [] : clone(RECOMMENDATIONS);
let rules = EMPTY_DEMO ? [] : clone(PRICING_RULES);
let executions = EMPTY_DEMO ? [] : clone(EXECUTIONS);
let jobs = EMPTY_DEMO ? [] : clone(PRICING_JOBS);

function paginate<T>(items: T[], page = 1, pageSize = 10): Paged<T> {
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * pageSize;
  return {
    data: items.slice(start, start + pageSize),
    meta: { page: safePage, pageSize, total, totalPages },
  };
}

const roundUpTo = (value: number, step: number) => Math.ceil(value / step) * step;

export interface LoginResult {
  user: User;
  token: string;
}

export async function login(email: string, password: string): Promise<LoginResult> {
  await wait(420);
  const found = DEMO_USERS.find(
    (u) => u.email.toLowerCase() === email.trim().toLowerCase(),
  );
  // Password is checked before the account status so the message never
  // reveals whether an email exists (UI-01).
  if (!found || found.password !== password) {
    throw new Error('Email hoặc mật khẩu không đúng.');
  }
  if (!found.isActive) throw new Error('Tài khoản đã bị vô hiệu hóa.');
  const { password: _pw, ...user } = found;
  return { user: clone(user), token: `demo.${found.id}` };
}

export async function getDashboard(): Promise<DashboardSummary> {
  await wait();
  if (EMPTY_DEMO) {
    return clone({
      revenue: 0,
      grossProfit: 0,
      margin: 0,
      skusBelowFloor: 0,
      lowStockCount: 0,
      pendingApprovals: 0,
      revenueTrend: [],
      profitByChannel: [],
      priceVsCompetitor: [],
    });
  }
  return clone(DASHBOARD);
}

export async function listProducts(params: {
  q?: string;
  categoryId?: string;
  supplierId?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}): Promise<Paged<Product>> {
  await wait();
  const q = params.q?.trim().toLowerCase() ?? '';
  const items = (EMPTY_DEMO ? [] : PRODUCTS).filter((p) => {
    if (q && !`${p.skuCode} ${p.name}`.toLowerCase().includes(q)) return false;
    if (params.categoryId && p.categoryId !== params.categoryId) return false;
    if (params.supplierId && p.supplierId !== params.supplierId) return false;
    if (params.status && p.status !== params.status) return false;
    return true;
  });
  return paginate(clone(items), params.page, params.pageSize ?? 10);
}

export interface ProductDetail {
  product: Product;
  inventory: InventoryBalance | null;
  recommendations: Recommendation[];
  listings: ChannelListing[];
}

export async function getProductDetail(id: string): Promise<ProductDetail | null> {
  await wait();
  if (EMPTY_DEMO) return null;
  const product = PRODUCTS.find((p) => p.id === id);
  if (!product) return null;
  return clone({
    product,
    inventory: INVENTORY.find((i) => i.skuCode === product.skuCode) ?? null,
    recommendations: recommendations
      .filter((r) => r.skuId === product.id)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt)),
    listings: CHANNEL_LISTINGS.filter((l) => l.skuId === product.id),
  });
}

export async function listSuppliers(): Promise<Supplier[]> {
  await wait();
  return clone(EMPTY_DEMO ? [] : SUPPLIERS);
}

export async function listChannels(): Promise<Channel[]> {
  await wait();
  return clone(EMPTY_DEMO ? [] : CHANNELS);
}

export interface ConnectionTest {
  ok: boolean;
  mode: Channel['integrationMode'];
  message: string;
  checkedAt: string;
}

/**
 * Channel connection test. Without credentials this only exercises the
 * SIMULATED adapter — the UI must never claim a live call happened
 * (SPEC §2.1, BUSINESS_RULES §6).
 */
export async function testChannelConnection(channelId: string): Promise<ConnectionTest> {
  await wait(600);
  const channel = CHANNELS.find((c) => c.id === channelId);
  if (!channel) throw new Error('Không tìm thấy kênh.');
  return {
    ok: channel.connectionStatus !== 'ERROR',
    mode: channel.integrationMode,
    message:
      channel.integrationMode === 'LIVE'
        ? 'Adapter LIVE phản hồi. Không gửi thay đổi giá trong lần kiểm tra này.'
        : 'Không có credential — đã kiểm tra adapter giả lập, không gọi sàn.',
    checkedAt: new Date().toISOString(),
  };
}

export async function listChannelListings(params: {
  q?: string;
  channelId?: string;
  syncStatus?: string;
  page?: number;
  pageSize?: number;
}): Promise<Paged<ChannelListing>> {
  await wait();
  const q = params.q?.trim().toLowerCase() ?? '';
  const items = (EMPTY_DEMO ? [] : CHANNEL_LISTINGS).filter((l) => {
    if (
      q &&
      !`${l.skuCode} ${l.productName} ${l.externalListingId}`
        .toLowerCase()
        .includes(q)
    )
      return false;
    if (params.channelId && l.channelId !== params.channelId) return false;
    if (params.syncStatus && l.syncStatus !== params.syncStatus) return false;
    return true;
  });
  return paginate(clone(items), params.page, params.pageSize ?? 10);
}

export async function listChannelFees(): Promise<ChannelFee[]> {
  await wait();
  return clone(EMPTY_DEMO ? [] : CHANNEL_FEES);
}

export async function listCompetitors(): Promise<Competitor[]> {
  await wait();
  return clone(EMPTY_DEMO ? [] : COMPETITORS);
}

export async function listCompetitorPrices(params: {
  q?: string;
  marketplace?: string;
  sourceType?: string;
  staleOnly?: boolean;
  page?: number;
  pageSize?: number;
}): Promise<Paged<CompetitorPrice>> {
  await wait();
  const q = params.q?.trim().toLowerCase() ?? '';
  const items = (EMPTY_DEMO ? [] : COMPETITOR_PRICES).filter((p) => {
    if (q && !`${p.skuCode} ${p.productName} ${p.competitorName}`.toLowerCase().includes(q))
      return false;
    if (params.marketplace && p.marketplaceCode !== params.marketplace) return false;
    if (params.sourceType && p.sourceType !== params.sourceType) return false;
    if (params.staleOnly) {
      const ageHours = (Date.now() - new Date(p.observedAt).getTime()) / 36e5;
      if (ageHours <= COMPETITOR_MAX_AGE_HOURS) return false;
    }
    return true;
  });
  return paginate(clone(items), params.page, params.pageSize ?? 10);
}

export async function listRecommendations(params: {
  status?: string;
  q?: string;
  page?: number;
  pageSize?: number;
}): Promise<Paged<Recommendation>> {
  await wait();
  const q = params.q?.trim().toLowerCase() ?? '';
  const items = recommendations.filter((r) => {
    if (params.status && r.status !== params.status) return false;
    if (q && !`${r.skuCode} ${r.productName} ${r.id}`.toLowerCase().includes(q)) return false;
    return true;
  });
  return paginate(clone(items), params.page, params.pageSize ?? 10);
}

export async function getRecommendation(id: string): Promise<Recommendation | null> {
  await wait();
  const found = recommendations.find((r) => r.id === id);
  return found ? clone(found) : null;
}

export async function updateRecommendationStatus(
  id: string,
  status: Recommendation['status'],
): Promise<void> {
  await wait(260);
  const found = recommendations.find((r) => r.id === id);
  if (!found) throw new Error('Không tìm thấy đề xuất.');
  if (found.status === 'EXPIRED') {
    throw new Error('Đề xuất đã hết hạn — cần chạy lại định giá.');
  }
  recommendations = recommendations.map((r) => (r.id === id ? { ...r, status } : r));
}

export async function listRules(): Promise<PricingRule[]> {
  await wait();
  return clone(rules);
}

export async function setRuleStatus(
  id: string,
  status: PricingRule['status'],
): Promise<void> {
  await wait(260);
  const rule = rules.find((r) => r.id === id);
  if (!rule) throw new Error('Không tìm thấy quy tắc.');
  if (rule.ruleType === 'MARGIN_GUARD') {
    throw new Error('Margin Guard là rào chắn hệ thống, không thể tắt từ UI.');
  }
  if (rule.status === 'ARCHIVED') {
    throw new Error('Quy tắc đã lưu trữ, không thể kích hoạt lại.');
  }
  if (status === 'ACTIVE') {
    // BUSINESS_RULES §3 — cannot activate without scope, window and guards.
    const missing: string[] = [];
    if (!rule.scopeLabel) missing.push('phạm vi');
    if (!rule.startsAt) missing.push('thời gian bắt đầu');
    if (!(rule.minMargin > 0)) missing.push('biên tối thiểu');
    if (!(rule.maxPriceChangePct > 0)) missing.push('giới hạn biến động');
    if (missing.length > 0) {
      throw new Error(`Không thể kích hoạt: thiếu ${missing.join(', ')}.`);
    }
  }
  rules = rules.map((r) => (r.id === id ? { ...r, status } : r));
}

export async function listExecutions(params: {
  status?: string;
  page?: number;
  pageSize?: number;
}): Promise<Paged<ExecutionRun>> {
  await wait();
  const items = executions.filter(
    (e) => !params.status || e.status === params.status,
  );
  return paginate(clone(items), params.page, params.pageSize ?? 10);
}

export async function retryExecution(id: string): Promise<void> {
  await wait(300);
  const run = executions.find((e) => e.id === id);
  if (!run) throw new Error('Không tìm thấy tác vụ.');
  if (run.status !== 'FAILED') {
    throw new Error('Chỉ thử lại được tác vụ đang ở trạng thái thất bại.');
  }
  if (run.attempts >= MAX_ATTEMPTS) {
    throw new Error(
      `Đã đạt giới hạn ${MAX_ATTEMPTS} lần thử. Tạo tác vụ khôi phục thay vì retry.`,
    );
  }
  executions = executions.map((e) =>
    e.id === id
      ? {
          ...e,
          status: 'QUEUED',
          attempts: e.attempts + 1,
          errorCode: null,
          updatedAt: new Date().toISOString(),
        }
      : e,
  );
}

export async function cancelExecution(id: string): Promise<void> {
  await wait(260);
  const run = executions.find((e) => e.id === id);
  if (!run) throw new Error('Không tìm thấy tác vụ.');
  if (run.status !== 'QUEUED') {
    throw new Error('Chỉ huỷ được tác vụ đang chờ trong hàng đợi.');
  }
  executions = executions.map((e) =>
    e.id === id
      ? { ...e, status: 'CANCELLED', updatedAt: new Date().toISOString() }
      : e,
  );
}

export async function listAuditLogs(page = 1, pageSize = 10): Promise<Paged<AuditLog>> {
  await wait();
  return paginate(clone(EMPTY_DEMO ? [] : AUDIT_LOGS), page, pageSize);
}

export async function listUsers(): Promise<User[]> {
  await wait();
  return EMPTY_DEMO
    ? []
    : DEMO_USERS.map(({ password: _pw, ...u }) => clone(u));
}

export async function listInventory(q = ''): Promise<typeof INVENTORY> {
  await wait();
  if (EMPTY_DEMO) return clone([]);
  const needle = q.trim().toLowerCase();
  return clone(
    INVENTORY.filter(
      (i) =>
        !needle ||
        `${i.skuCode} ${i.productName} ${i.warehouseName}`.toLowerCase().includes(needle),
    ),
  );
}

/* --- Smart Pricing (rule-based, deterministic) -------------------------- */

export interface PricingRunInput {
  skuIds: string[];
  channelId: string;
  objective: 'PROFIT' | 'COMPETITIVE' | 'CLEAR_STOCK';
  targetMargin: number;
  mode: 'RULE_BASED' | 'ML_ASSISTED';
  competitorStrategy: 'IGNORE' | 'STAY_WITHIN_RANGE' | 'MATCH_MEDIAN';
  stockStrategy: 'NEUTRAL' | 'CLEAR_SLOW_MOVING';
  effectiveAt: string | null;
}

export interface PricingPreviewRow {
  skuId: string;
  skuCode: string;
  productName: string;
  unitCost: number;
  currentPrice: number;
  feeRate: number;
  competitorMedian: number | null;
  competitorObservedAt: string | null;
  competitorSampleCount: number;
}

interface CompetitorSignal {
  median: number | null;
  observedAt: string | null;
  sampleCount: number;
}

/** Valid competitor median — fresh, not flagged as outlier (AI_PRICING §7). */
function competitorSignal(skuId: string, marketplaceCode: string): CompetitorSignal {
  const observations = COMPETITOR_PRICES.filter(
    (o) => o.skuId === skuId && o.marketplaceCode === marketplaceCode && !o.isOutlier,
  ).filter(
    (o) =>
      (Date.now() - new Date(o.observedAt).getTime()) / 36e5 <=
      COMPETITOR_MAX_AGE_HOURS,
  );
  const prices = observations
    .map((o) => o.effectivePrice ?? o.listedPrice)
    .sort((a, b) => a - b);
  if (prices.length === 0) {
    return { median: null, observedAt: null, sampleCount: 0 };
  }
  const mid = Math.floor(prices.length / 2);
  const median =
    prices.length % 2 === 1
      ? prices[mid]!
      : (prices[mid - 1]! + prices[mid]!) / 2;
  const latest = observations.reduce((a, b) =>
    new Date(a.observedAt) > new Date(b.observedAt) ? a : b,
  );
  return {
    median: Math.round(median / PRICE_INCREMENT) * PRICE_INCREMENT,
    observedAt: latest.observedAt,
    sampleCount: observations.length,
  };
}

export async function getPricingPreview(input: {
  skuIds: string[];
  channelId: string;
}): Promise<PricingPreviewRow[]> {
  await wait(200);
  const channel = CHANNELS.find((c) => c.id === input.channelId);
  if (!channel) throw new Error('Không tìm thấy kênh.');
  return input.skuIds.flatMap((skuId) => {
    const product = PRODUCTS.find((p) => p.id === skuId);
    if (!product) return [];
    const signal = competitorSignal(product.id, channel.code);
    return [
      {
        skuId: product.id,
        skuCode: product.skuCode,
        productName: product.name,
        unitCost: product.unitCost,
        currentPrice: product.currentPrice,
        feeRate: channel.feeRate,
        competitorMedian: signal.median,
        competitorObservedAt: signal.observedAt,
        competitorSampleCount: signal.sampleCount,
      },
    ];
  });
}

export interface PricingRunResult {
  jobId: string;
  requestedCount: number;
  results: Recommendation[];
  noSafePriceSkuCodes: string[];
}

const plainFactors = (
  unitCost: number,
  feeRate: number,
  floor: number,
  median: number | null,
): Explanation['factors'] => [
  {
    key: 'unit_cost',
    label: 'Giá vốn đơn vị',
    value: String(unitCost),
    format: 'money',
    impact: 'raises_floor',
  },
  {
    key: 'channel_fee_rate',
    label: 'Phí kênh',
    value: String(feeRate),
    format: 'percent',
    impact: 'raises_floor',
  },
  {
    key: 'floor_price',
    label: 'Giá sàn',
    value: String(floor),
    format: 'money',
    impact: 'raises_floor',
  },
  ...(median !== null
    ? [
        {
          key: 'competitor_median',
          label: 'Trung vị đối thủ',
          value: String(median),
          format: 'money' as const,
          impact: 'anchors_price' as const,
        },
      ]
    : []),
];

export async function runPricing(input: PricingRunInput): Promise<PricingRunResult> {
  await wait(900);
  const channel = CHANNELS.find((c) => c.id === input.channelId);
  if (!channel) throw new Error('Không tìm thấy kênh.');
  const denom = 1 - channel.feeRate - input.targetMargin;
  const createdAt = new Date().toISOString();
  const expiresAt = new Date(Date.now() + 24 * 36e5).toISOString();
  const results: Recommendation[] = [];
  const noSafePriceSkuCodes: string[] = [];

  for (const skuId of input.skuIds) {
    const product = PRODUCTS.find((p) => p.id === skuId);
    if (!product) continue;
    if (denom <= 0) {
      noSafePriceSkuCodes.push(product.skuCode);
      continue;
    }

    const unitCost = product.unitCost;
    const current = product.currentPrice;
    const floor = roundUpTo(unitCost / denom, PRICE_INCREMENT);
    const signal =
      input.competitorStrategy === 'IGNORE'
        ? { median: null, observedAt: null, sampleCount: 0 }
        : competitorSignal(product.id, channel.code);
    const anchor = signal.median ?? current;

    let candidate =
      input.objective === 'PROFIT'
        ? Math.max(anchor, floor) * 1.03
        : input.objective === 'COMPETITIVE'
          ? anchor * 0.98
          : anchor * 0.92;

    // CLEAR_STOCK only bites when the analyst opted in.
    if (
      input.objective === 'CLEAR_STOCK' &&
      input.stockStrategy === 'NEUTRAL'
    ) {
      candidate = anchor;
    }

    // Clamp to the allowed change window before enforcing the floor.
    const lowerBound = current * (1 - MAX_PRICE_CHANGE_PCT);
    const upperBound = current * (1 + MAX_PRICE_CHANGE_PCT);
    candidate = Math.min(Math.max(candidate, lowerBound), upperBound);

    const clampedBelowFloor = candidate < floor;
    let price = roundUpTo(candidate, PRICE_INCREMENT);
    if (price < floor) price = floor;

    const maxChangePassed = Math.abs(price - current) / current <= MAX_PRICE_CHANGE_PCT;
    const profit = price - unitCost - Math.round(price * channel.feeRate);
    const margin = price > 0 ? profit / price : 0;
    const dataQuality: Recommendation['dataQuality'] =
      signal.sampleCount === 0 ? 'LOW' : signal.sampleCount >= 2 ? 'HIGH' : 'MEDIUM';

    results.push({
      id: `rec-${Date.now()}-${results.length + 1}`,
      skuId: product.id,
      skuCode: product.skuCode,
      productName: product.name,
      channelId: channel.id,
      channelName: channel.name,
      status: 'DRAFT',
      currentPrice: current,
      floorPrice: floor,
      recommendedPrice: price,
      expectedProfitPerUnit: profit,
      expectedMargin: Number(margin.toFixed(4)),
      unitCost,
      channelFeeRate: channel.feeRate,
      competitorMedian: signal.median,
      targetMargin: input.targetMargin,
      dataQuality,
      algorithmType: input.mode,
      algorithmVersion: 'rule-v1.2.0',
      explanation: {
        summary: clampedBelowFloor
          ? 'Giới hạn biến động giá khiến giá tối ưu nằm dưới giá sàn — đã kéo về giá sàn và cần người duyệt.'
          : signal.median !== null
            ? 'Giá đề xuất neo theo trung vị đối thủ còn mới và không thấp hơn giá sàn.'
            : 'Thiếu tín hiệu đối thủ còn mới — giá đề xuất neo theo giá hiện tại và giá sàn.',
        factors: plainFactors(unitCost, channel.feeRate, floor, signal.median),
        constraints: {
          floorPassed: price >= floor,
          maxChangePassed,
          competitorFresh: signal.median !== null,
        },
        dataQuality,
      },
      createdBy: 'Bạn (DEMO)',
      createdAt,
      expiresAt,
    });
  }

  const jobId = `job-${Date.now()}`;
  jobs = [
    {
      id: jobId,
      channelName: channel.name,
      objective: input.objective,
      mode: input.mode,
      targetMargin: input.targetMargin,
      skuCount: input.skuIds.length,
      resultCount: results.length,
      noSafePriceCount: noSafePriceSkuCodes.length,
      status:
        results.length === 0
          ? 'FAILED'
          : noSafePriceSkuCodes.length > 0
            ? 'PARTIAL'
            : 'COMPLETED',
      createdAt,
    },
    ...jobs,
  ];
  recommendations = [...results, ...recommendations];

  return {
    jobId,
    requestedCount: input.skuIds.length,
    results: clone(results),
    noSafePriceSkuCodes,
  };
}

export async function listPricingJobs(): Promise<PricingJob[]> {
  await wait();
  return clone(EMPTY_DEMO ? [] : jobs);
}

export async function listPricingSchedules(): Promise<PricingSchedule[]> {
  await wait();
  return clone(EMPTY_DEMO ? [] : PRICING_SCHEDULES);
}

/* --- Collected real data (TikTok Shop VN via ReefAPI) -------------------- */

export function collectedMeta(): CollectedMeta {
  if (EMPTY_DEMO) {
    return {
      marketplaceCode: 'TIKTOK_SHOP',
      market: 'vn',
      collectedAt: '',
      source: '',
      categoryCounts: {},
      total: 0,
      note: 'Demo empty state',
    };
  }
  return COLLECTED_COMPETITOR_META;
}

export interface CollectedStats {
  total: number;
  outlierCount: number;
  categoryCount: number;
  categoryNames: Record<string, string>;
}

/** Aggregate numbers for the collected-data page, so the page never has to
 * read the raw mock module itself. */
export function collectedStats(): CollectedStats {
  if (EMPTY_DEMO) {
    return {
      total: 0,
      outlierCount: 0,
      categoryCount: 0,
      categoryNames: {},
    };
  }
  const categoryNames: Record<string, string> = {};
  for (const record of COLLECTED_COMPETITOR_PRICES) {
    categoryNames[record.categoryId] = record.categoryName;
  }
  return {
    total: COLLECTED_COMPETITOR_PRICES.length,
    outlierCount: COLLECTED_COMPETITOR_PRICES.filter((r) => r.isOutlier).length,
    categoryCount: Object.keys(categoryNames).length,
    categoryNames,
  };
}

export async function listCollectedCompetitorPrices(params: {
  q?: string;
  categoryId?: string;
  page?: number;
  pageSize?: number;
}): Promise<Paged<CollectedCompetitorPrice>> {
  await wait();
  if (EMPTY_DEMO) return paginate([], params.page, params.pageSize ?? 10);
  const q = params.q?.trim().toLowerCase() ?? '';
  const items = COLLECTED_COMPETITOR_PRICES.filter((r) => {
    if (
      q &&
      !`${r.productTitle} ${r.sellerName} ${r.externalProductId}`
        .toLowerCase()
        .includes(q)
    )
      return false;
    if (params.categoryId && r.categoryId !== params.categoryId) return false;
    return true;
  });
  return paginate(clone(items), params.page, params.pageSize ?? 10);
}
