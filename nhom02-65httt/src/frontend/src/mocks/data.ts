/*
 * DEMO dataset. Every record here is fabricated for the MVP demo and must be
 * labelled DEMO in the UI (SPEC.md §7.8, AI_AGENT_GUIDE.md §3).
 * Isolated from any future API layer: components never import this directly,
 * they go through the mock API in `mocks/api.ts`.
 */
import type {
  AuditLog,
  Category,
  Channel,
  ChannelFee,
  ChannelListing,
  Explanation,
  Competitor,
  CompetitorPrice,
  DashboardSummary,
  ExecutionRun,
  InventoryBalance,
  PricingJob,
  PricingRule,
  PricingSchedule,
  Product,
  Recommendation,
  RecommendationStatus,
  Supplier,
  User,
} from '@/types/domain';

const now = Date.now();
const hoursAgo = (h: number) => new Date(now - h * 36e5).toISOString();
const daysAgo = (d: number) => hoursAgo(d * 24);

export const DEMO_USERS: (User & { password: string })[] = [
  {
    id: 'u-admin',
    fullName: 'Nguyễn Quản Trị',
    email: 'admin@erp.demo',
    role: 'ADMIN',
    isActive: true,
    lastLoginAt: hoursAgo(2),
    createdAt: daysAgo(180),
    password: 'demo1234',
  },
  {
    id: 'u-manager',
    fullName: 'Trần Thị Mai',
    email: 'manager@erp.demo',
    role: 'MANAGER',
    isActive: true,
    lastLoginAt: hoursAgo(5),
    createdAt: daysAgo(150),
    password: 'demo1234',
  },
  {
    id: 'u-analyst',
    fullName: 'Lê Văn Hùng',
    email: 'analyst@erp.demo',
    role: 'PRICING_ANALYST',
    isActive: true,
    lastLoginAt: hoursAgo(1),
    createdAt: daysAgo(120),
    password: 'demo1234',
  },
  {
    id: 'u-inventory',
    fullName: 'Phạm Thu Hà',
    email: 'inventory@erp.demo',
    role: 'INVENTORY_STAFF',
    isActive: true,
    lastLoginAt: hoursAgo(26),
    createdAt: daysAgo(90),
    password: 'demo1234',
  },
  {
    id: 'u-viewer',
    fullName: 'Đỗ Minh Khoa',
    email: 'viewer@erp.demo',
    role: 'VIEWER',
    isActive: true,
    lastLoginAt: hoursAgo(72),
    createdAt: daysAgo(60),
    password: 'demo1234',
  },
];

export const CATEGORIES: Category[] = [
  { id: 'cat-1', name: 'Thời trang' },
  { id: 'cat-2', name: 'Điện tử' },
  { id: 'cat-3', name: 'Gia dụng' },
  { id: 'cat-4', name: 'Làm đẹp' },
  { id: 'cat-5', name: 'Thể thao' },
];

const SUPPLIER_SEED: Omit<Supplier, 'skuCount'>[] = [
  {
    id: 'sup-1',
    supplierCode: 'NCC-HN-001',
    name: 'Công ty TNHH May mặc Hà Nội',
    contactName: 'Nguyễn Thị Lan',
    email: 'lan@mayhanoi.vn',
    phone: '024 3825 1122',
    lastQuotedAt: daysAgo(2),
    status: 'ACTIVE',
  },
  {
    id: 'sup-2',
    supplierCode: 'NCC-HCM-014',
    name: 'Thiết bị số Sài Gòn',
    contactName: 'Trương Quốc Bảo',
    email: 'bao@tbsaigon.vn',
    phone: '028 7300 4455',
    lastQuotedAt: daysAgo(9),
    status: 'ACTIVE',
  },
  {
    id: 'sup-3',
    supplierCode: 'NCC-DN-007',
    name: 'Gia dụng Đà Nẵng',
    contactName: 'Hồ Văn Tâm',
    email: 'tam@giaudungdn.vn',
    phone: '0236 388 7766',
    lastQuotedAt: daysAgo(41),
    status: 'ACTIVE',
  },
  {
    id: 'sup-4',
    supplierCode: 'NCC-HN-029',
    name: 'Mỹ phẩm An Nhiên',
    contactName: 'Vũ Thị Hạnh',
    email: 'hanh@annhien.vn',
    phone: '024 6688 9090',
    lastQuotedAt: daysAgo(15),
    status: 'INACTIVE',
  },
];

const SUPPLIER_BY_CATEGORY: Record<string, string> = {
  'cat-1': 'sup-1',
  'cat-5': 'sup-1',
  'cat-2': 'sup-2',
  'cat-3': 'sup-3',
  'cat-4': 'sup-4',
};

const PRODUCT_SEED: { name: string; category: string; unit: string }[] = [
  { name: 'Áo thun cotton basic', category: 'cat-1', unit: 'cái' },
  { name: 'Quần jean slim fit', category: 'cat-1', unit: 'cái' },
  { name: 'Áo khoác gió unisex', category: 'cat-1', unit: 'cái' },
  { name: 'Váy midi hoa nhí', category: 'cat-1', unit: 'cái' },
  { name: 'Sơ mi linen nam', category: 'cat-1', unit: 'cái' },
  { name: 'Tai nghe bluetooth TWS', category: 'cat-2', unit: 'bộ' },
  { name: 'Sạc dự phòng 20.000mAh', category: 'cat-2', unit: 'cái' },
  { name: 'Chuột không dây văn phòng', category: 'cat-2', unit: 'cái' },
  { name: 'Bàn phím cơ mini 65%', category: 'cat-2', unit: 'cái' },
  { name: 'Đồng hồ thông minh thể thao', category: 'cat-2', unit: 'cái' },
  { name: 'Nồi chiên không dầu 5L', category: 'cat-3', unit: 'cái' },
  { name: 'Bộ dao kéo nhà bếp', category: 'cat-3', unit: 'bộ' },
  { name: 'Bình giữ nhiệt 1L', category: 'cat-3', unit: 'cái' },
  { name: 'Máy hút bụi cầm tay', category: 'cat-3', unit: 'cái' },
  { name: 'Kệ để đồ đa năng', category: 'cat-3', unit: 'cái' },
  { name: 'Serum vitamin C 30ml', category: 'cat-4', unit: 'chai' },
  { name: 'Kem chống nắng SPF50', category: 'cat-4', unit: 'tuýp' },
  { name: 'Sữa rửa mặt dịu nhẹ', category: 'cat-4', unit: 'tuýp' },
  { name: 'Mặt nạ dưỡng ẩm (hộp 10)', category: 'cat-4', unit: 'hộp' },
  { name: 'Nước tẩy trang 400ml', category: 'cat-4', unit: 'chai' },
  { name: 'Thảm yoga TPE 6mm', category: 'cat-5', unit: 'cái' },
  { name: 'Tạ tay 5kg (đôi)', category: 'cat-5', unit: 'đôi' },
  { name: 'Dây nhảy thể lực', category: 'cat-5', unit: 'cái' },
  { name: 'Bình nước thể thao 750ml', category: 'cat-5', unit: 'cái' },
  { name: 'Găng tay tập gym', category: 'cat-5', unit: 'đôi' },
  { name: 'Áo thun thể thao nữ', category: 'cat-1', unit: 'cái' },
  { name: 'Quần short kaki nam', category: 'cat-1', unit: 'cái' },
  { name: 'Balo laptop 15.6 inch', category: 'cat-2', unit: 'cái' },
  { name: 'Đèn bàn chống cận', category: 'cat-3', unit: 'cái' },
  { name: 'Máy sấy tóc 1800W', category: 'cat-3', unit: 'cái' },
];

const catName = (id: string) => CATEGORIES.find((c) => c.id === id)?.name ?? '—';

export const PRODUCTS: Product[] = PRODUCT_SEED.map((seed, i) => {
  const unitCost = 45_000 + i * 11_000;
  const currentPrice = Math.round((unitCost * (1.55 + (i % 5) * 0.08)) / 1000) * 1000;
  const supplierId = SUPPLIER_BY_CATEGORY[seed.category] ?? null;
  // Deterministic demo split of the landed cost (UI-03 form fields).
  const purchase = Math.round(unitCost * 0.9);
  const inbound = Math.round(unitCost * 0.06);
  const packaging = Math.round(unitCost * 0.04);
  return {
    id: `sku-${i + 1}`,
    skuCode: `SKU-${String(1000 + i)}`,
    name: seed.name,
    variantName: i % 4 === 0 ? 'Tiêu chuẩn' : null,
    categoryId: seed.category,
    categoryName: catName(seed.category),
    unit: seed.unit,
    currentPrice,
    unitCost,
    costBreakdown: {
      purchase,
      inbound,
      packaging,
      other: unitCost - purchase - inbound - packaging,
    },
    supplierId,
    supplierName: SUPPLIER_SEED.find((s) => s.id === supplierId)?.name ?? null,
    availableQty: null,
    status: i === 27 ? 'ARCHIVED' : 'ACTIVE',
    updatedAt: hoursAgo(3 + (i % 40)),
  };
});

/** SKU count is derived from PRODUCTS so the number can never drift. */
export const SUPPLIERS: Supplier[] = SUPPLIER_SEED.map((s) => ({
  ...s,
  skuCount: PRODUCTS.filter((p) => p.supplierId === s.id).length,
}));

export const INVENTORY: InventoryBalance[] = PRODUCTS.slice(0, 24).map((p, i) => {
  const onHand = 20 + ((i * 37) % 400);
  const reserved = Math.floor(onHand * 0.15);
  return {
    id: `inv-${i + 1}`,
    skuCode: p.skuCode,
    productName: p.name,
    warehouseName: i % 3 === 0 ? 'Kho Hà Nội' : i % 3 === 1 ? 'Kho HCM' : 'Kho Đà Nẵng',
    onHandQty: onHand,
    reservedQty: reserved,
    // Every 4th SKU sits below its reorder point, so the low-stock state is
    // reachable in the demo instead of being an empty table.
    reorderPoint: i % 4 === 0 ? Math.round(onHand * 1.12) : Math.round(onHand * 0.28),
    updatedAt: hoursAgo(1 + (i % 6)),
  };
});

const inventoryBySku = new Map(INVENTORY.map((i) => [i.skuCode, i]));
for (const product of PRODUCTS) {
  const balance = inventoryBySku.get(product.skuCode);
  product.availableQty = balance
    ? balance.onHandQty - balance.reservedQty
    : null;
}

export const CHANNELS: Channel[] = [
  {
    id: 'ch-shopee',
    code: 'SHOPEE',
    name: 'Shopee',
    integrationMode: 'SIMULATED',
    connectionStatus: 'DEMO',
    isActive: true,
    listingCount: 180,
    feeRate: 0.12,
  },
  {
    id: 'ch-tiktok',
    code: 'TIKTOK_SHOP',
    name: 'TikTok Shop',
    integrationMode: 'SIMULATED',
    connectionStatus: 'DEMO',
    isActive: true,
    listingCount: 142,
    feeRate: 0.14,
  },
  {
    id: 'ch-lazada',
    code: 'LAZADA',
    name: 'Lazada',
    integrationMode: 'SIMULATED',
    connectionStatus: 'NOT_CONNECTED',
    isActive: true,
    listingCount: 96,
    feeRate: 0.1,
  },
  {
    id: 'ch-web',
    code: 'WEBSITE',
    name: 'Website / Other',
    integrationMode: 'LIVE',
    connectionStatus: 'CONNECTED',
    isActive: true,
    listingCount: 210,
    feeRate: 0.03,
  },
];

export const COMPETITORS: Competitor[] = [
  { id: 'cmp-1', name: 'Shop Thời Trang A', marketplaceCode: 'SHOPEE', storeUrl: 'https://example.com/a', status: 'TRACKING' },
  { id: 'cmp-2', name: 'Tổng Kho Điện Tử B', marketplaceCode: 'SHOPEE', storeUrl: 'https://example.com/b', status: 'TRACKING' },
  { id: 'cmp-3', name: 'Gia Dụng Tiện Ích C', marketplaceCode: 'LAZADA', storeUrl: 'https://example.com/c', status: 'TRACKING' },
  { id: 'cmp-4', name: 'Beauty Store D', marketplaceCode: 'TIKTOK_SHOP', storeUrl: 'https://example.com/d', status: 'PAUSED' },
  { id: 'cmp-5', name: 'Sport Zone E', marketplaceCode: 'SHOPEE', storeUrl: 'https://example.com/e', status: 'TRACKING' },
];

export const COMPETITOR_PRICES: CompetitorPrice[] = PRODUCTS.slice(0, 20).map((p, i) => {
  const competitor = COMPETITORS[i % COMPETITORS.length]!;
  const base = Math.round((p.currentPrice * (0.86 + ((i % 7) * 0.04))) / 1000) * 1000;
  return {
    id: `cp-${i + 1}`,
    skuId: p.id,
    skuCode: p.skuCode,
    productName: p.name,
    competitorId: competitor.id,
    competitorName: competitor.name,
    marketplaceCode: competitor.marketplaceCode,
    listedPrice: base,
    effectivePrice: i % 3 === 0 ? Math.round(base * 0.95) : null,
    sourceType: i % 5 === 0 ? 'CSV' : i % 4 === 0 ? 'MANUAL' : 'DEMO',
    sourceName: i % 4 === 0 ? 'Nhập tay' : 'CSV import',
    observedAt: hoursAgo(i % 6 === 0 ? 30 : 2 + i),
    confidence: Number((0.7 + ((i % 4) * 0.07)).toFixed(2)),
    isOutlier: i === 7 || i === 15,
  };
});

const roundUp1000 = (v: number) => Math.ceil(v / 1000) * 1000;

/**
 * Explanation is built from the same numbers the recommendation was computed
 * from, so the UI can never show a cost or fee that contradicts the snapshot
 * (AI_PRICING §10, §12).
 */
const EXPLANATION = (
  floor: number,
  compMedian: number | null,
  unitCost: number,
  feeRate: number,
  recommended: number,
  current: number,
): Explanation => ({
  summary: compMedian
    ? 'Giá đề xuất bám trung vị đối thủ nhưng không thấp hơn giá sàn bảo vệ biên lợi nhuận.'
    : 'Thiếu tín hiệu đối thủ còn mới — giá đề xuất neo theo giá sàn và giá hiện tại.',
  factors: [
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
    ...(compMedian
      ? [
          {
            key: 'competitor_median',
            label: 'Trung vị đối thủ',
            value: String(compMedian),
            format: 'money' as const,
            impact: 'anchors_price' as const,
          },
        ]
      : []),
  ],
  constraints: {
    floorPassed: recommended >= floor,
    maxChangePassed: current > 0 ? Math.abs(recommended - current) / current <= 0.2 : true,
    competitorFresh: compMedian !== null,
  },
  dataQuality: compMedian === null ? 'MEDIUM' : 'HIGH',
});

const REC_STATUSES: RecommendationStatus[] = [
  'PENDING_APPROVAL',
  'PENDING_APPROVAL',
  'APPROVED',
  'DRAFT',
  'EXECUTED',
  'REJECTED',
  'PENDING_APPROVAL',
  'EXPIRED',
  'APPROVED',
  'PENDING_APPROVAL',
  'DRAFT',
  'EXECUTED',
];

export const RECOMMENDATIONS: Recommendation[] = REC_STATUSES.map((status, i) => {
  const p = PRODUCTS[i]!;
  const channel = CHANNELS[i % 3]!;
  const targetMargin = 0.18;
  const current = p.currentPrice;
  // P_floor = (C + F) / (1 - f - m) — AI_PRICING §5, F = 0 for the demo.
  const floor = roundUp1000(p.unitCost / (1 - channel.feeRate - targetMargin));
  const recommended = roundUp1000(floor * (1.04 + (i % 5) * 0.03));
  const profit = recommended - p.unitCost - Math.round(recommended * channel.feeRate);
  const hasFreshCompetitor = i !== 7 && i !== 10;
  const competitorMedian = hasFreshCompetitor ? roundUp1000(floor * 1.08) : null;
  const quality = !hasFreshCompetitor ? 'LOW' : i % 5 === 0 ? 'MEDIUM' : 'HIGH';
  return {
    id: `rec-${1000 + i}`,
    skuId: p.id,
    skuCode: p.skuCode,
    productName: p.name,
    channelId: channel.id,
    channelName: channel.name,
    status,
    currentPrice: current,
    floorPrice: floor,
    recommendedPrice: recommended,
    expectedProfitPerUnit: profit,
    expectedMargin: Number((profit / recommended).toFixed(4)),
    unitCost: p.unitCost,
    channelFeeRate: channel.feeRate,
    competitorMedian,
    targetMargin,
    dataQuality: quality,
    algorithmType: 'RULE_BASED',
    algorithmVersion: 'rule-v1.2.0',
    explanation: EXPLANATION(
      floor,
      competitorMedian,
      p.unitCost,
      channel.feeRate,
      recommended,
      current,
    ),
    createdBy: 'Lê Văn Hùng',
    createdAt: hoursAgo(1 + i * 3),
    expiresAt: hoursAgo(-20 + i),
  };
});

export const PRICING_RULES: PricingRule[] = [
  {
    id: 'rule-1',
    name: 'Margin Guard toàn hệ thống',
    ruleType: 'MARGIN_GUARD',
    priority: 1000,
    scopeLabel: 'Tất cả SKU · mọi kênh',
    minMargin: 0.15,
    maxPriceChangePct: 0.2,
    approvalRequired: true,
    status: 'ACTIVE',
    startsAt: daysAgo(30),
    endsAt: null,
  },
  {
    id: 'rule-2',
    name: 'Flash Sale cuối tuần',
    ruleType: 'FLASH_SALE',
    priority: 200,
    scopeLabel: 'Thời trang · Shopee',
    minMargin: 0.12,
    maxPriceChangePct: 0.25,
    approvalRequired: true,
    status: 'ACTIVE',
    startsAt: daysAgo(2),
    endsAt: hoursAgo(-48),
  },
  {
    id: 'rule-3',
    name: 'Bám giá đối thủ điện tử',
    ruleType: 'COMPETITOR_MATCH',
    priority: 150,
    scopeLabel: 'Điện tử · Shopee, Lazada',
    minMargin: 0.14,
    maxPriceChangePct: 0.1,
    approvalRequired: true,
    status: 'ACTIVE',
    startsAt: daysAgo(10),
    endsAt: null,
  },
  {
    id: 'rule-4',
    name: 'Xả kho tồn lâu',
    ruleType: 'CLEARANCE',
    priority: 120,
    scopeLabel: 'Gia dụng · tồn > 90 ngày',
    minMargin: 0.08,
    maxPriceChangePct: 0.3,
    approvalRequired: true,
    status: 'PAUSED',
    startsAt: daysAgo(20),
    endsAt: null,
  },
  {
    id: 'rule-5',
    name: 'Hớt váng sản phẩm mới',
    ruleType: 'SKIMMING',
    priority: 80,
    scopeLabel: 'Làm đẹp · 30 ngày đầu',
    minMargin: 0.22,
    maxPriceChangePct: 0.15,
    approvalRequired: false,
    status: 'DRAFT',
    startsAt: daysAgo(1),
    endsAt: null,
  },
];

export const EXECUTIONS: ExecutionRun[] = PRODUCTS.slice(0, 14).map((p, i) => {
  const status = (
    ['SUCCEEDED', 'SUCCEEDED', 'FAILED', 'RUNNING', 'PARTIAL', 'QUEUED', 'SUCCEEDED', 'CANCELLED'] as const
  )[i % 8];
  const createdAt = hoursAgo(1 + i * 2);
  return {
    id: `run-${2000 + i}`,
    skuCode: p.skuCode,
    channelName: CHANNELS[i % 4]!.name,
    mode: i % 5 === 0 ? 'LIVE' : 'SIMULATED',
    requestedPrice: Math.round((p.currentPrice * 1.06) / 1000) * 1000,
    previousPrice: p.currentPrice,
    status,
    attempts: status === 'FAILED' ? 3 : 1,
    errorCode: status === 'FAILED' ? 'PROVIDER_TIMEOUT' : null,
    idempotencyKey: `exec-${p.skuCode}-${1000 + i}`,
    createdAt,
    updatedAt: status === 'QUEUED' ? createdAt : hoursAgo(1 + i * 2 - 0.2),
  };
});

export const AUDIT_LOGS: AuditLog[] = [
  {
    id: 'al-1',
    actor: 'Trần Thị Mai',
    action: 'APPROVE_RECOMMENDATION',
    resourceType: 'pricing_recommendation',
    reason: 'Biên lợi nhuận hợp lý',
    requestId: 'req-7f2c1a90',
    beforeSummary: 'PENDING_APPROVAL',
    afterSummary: 'APPROVED',
    createdAt: hoursAgo(1),
  },
  {
    id: 'al-2',
    actor: 'Lê Văn Hùng',
    action: 'RUN_PRICING',
    resourceType: 'pricing_job',
    reason: null,
    requestId: 'req-3b81de04',
    beforeSummary: null,
    afterSummary: 'job-1001 · 6 SKU',
    createdAt: hoursAgo(2),
  },
  {
    id: 'al-3',
    actor: 'Phạm Thu Hà',
    action: 'ADJUST_INVENTORY',
    resourceType: 'inventory_balance',
    reason: 'Kiểm kê định kỳ',
    requestId: 'req-9c44abb1',
    beforeSummary: 'on_hand 120',
    afterSummary: 'on_hand 118',
    createdAt: hoursAgo(6),
  },
  {
    id: 'al-4',
    actor: 'Trần Thị Mai',
    action: 'ACTIVATE_RULE',
    resourceType: 'pricing_rule',
    reason: 'Chiến dịch cuối tuần',
    requestId: 'req-1d90fe27',
    beforeSummary: 'PAUSED',
    afterSummary: 'ACTIVE',
    createdAt: hoursAgo(14),
  },
  {
    id: 'al-5',
    actor: 'Nguyễn Quản Trị',
    action: 'UPDATE_USER_ROLE',
    resourceType: 'user',
    reason: 'Bổ sung analyst',
    requestId: 'req-5ab7c310',
    beforeSummary: 'VIEWER',
    afterSummary: 'PRICING_ANALYST',
    createdAt: daysAgo(1),
  },
  {
    id: 'al-6',
    actor: 'Lê Văn Hùng',
    action: 'IMPORT_COMPETITOR_PRICES',
    resourceType: 'import',
    reason: 'Cập nhật giá thị trường',
    requestId: 'req-2e6f8803',
    beforeSummary: null,
    afterSummary: '48 dòng hợp lệ',
    createdAt: daysAgo(2),
  },
];

/* --- Channel fee configuration (UI-13) --------------------------------- */

export const CHANNEL_FEES: ChannelFee[] = CHANNELS.map((c, i) => {
  const platform = Math.round(c.feeRate * 0.6 * 1000) / 1000;
  const payment = Math.round(c.feeRate * 0.3 * 1000) / 1000;
  const affiliate = Math.round((c.feeRate - platform - payment) * 1000) / 1000;
  return {
    channelId: c.id,
    channelName: c.name,
    totalRate: c.feeRate,
    effectiveFrom: daysAgo(30 + i * 5),
    source: i % 2 === 0 ? 'Hợp đồng kênh · nhập tay' : 'Bảng phí công bố',
    components: [
      { name: 'Phí nền tảng', type: 'PERCENT', value: platform, verified: true },
      { name: 'Phí thanh toán', type: 'PERCENT', value: payment, verified: i !== 2 },
      {
        name: 'Phí affiliate / voucher',
        type: 'PERCENT',
        value: affiliate,
        verified: i !== 2,
      },
    ],
  };
});

/* --- Channel listing mapping (UI-06) ----------------------------------- */

const SYNC_STATUSES = ['SYNCED', 'SYNCED', 'SYNCED', 'PENDING', 'ERROR'] as const;

export const CHANNEL_LISTINGS: ChannelListing[] = PRODUCTS.slice(0, 18).flatMap(
  (p, i) =>
    [CHANNELS[i % 3]!, CHANNELS[(i + 1) % 3]!].map((c, j) => ({
      id: `lst-${i + 1}-${j + 1}`,
      skuId: p.id,
      skuCode: p.skuCode,
      productName: p.name,
      channelId: c.id,
      channelName: c.name,
      externalListingId: `${c.code}-L${(i + 1) * 37 + j}`,
      externalSku: `${c.code}-${p.skuCode}`,
      currentPrice: roundUp1000(p.currentPrice * (1 + j * 0.02)),
      syncStatus: SYNC_STATUSES[(i + j) % SYNC_STATUSES.length]!,
      lastSyncedAt: hoursAgo(1 + ((i + j) % 9)),
    })),
);

/* --- Pricing automation jobs and schedules (UI-08 / FR-043) ------------ */

export const PRICING_JOBS: PricingJob[] = [
  {
    id: 'job-1001',
    channelName: 'Shopee',
    objective: 'PROFIT',
    mode: 'RULE_BASED',
    targetMargin: 0.18,
    skuCount: 6,
    resultCount: 6,
    noSafePriceCount: 0,
    status: 'COMPLETED',
    createdAt: hoursAgo(2),
  },
  {
    id: 'job-1000',
    channelName: 'TikTok Shop',
    objective: 'COMPETITIVE',
    mode: 'RULE_BASED',
    targetMargin: 0.22,
    skuCount: 4,
    resultCount: 3,
    noSafePriceCount: 1,
    status: 'PARTIAL',
    createdAt: daysAgo(1),
  },
];

export const PRICING_SCHEDULES: PricingSchedule[] = [
  {
    id: 'sch-1',
    name: 'Định giá lại hằng ngày',
    ruleName: 'Bám giá đối thủ điện tử',
    cronLabel: 'Mỗi ngày 08:00',
    mode: 'SIMULATED',
    nextRunAt: hoursAgo(-14),
    enabled: true,
  },
  {
    id: 'sch-2',
    name: 'Flash Sale cuối tuần',
    ruleName: 'Flash Sale cuối tuần',
    cronLabel: 'Thứ 6 20:00',
    mode: 'SIMULATED',
    nextRunAt: hoursAgo(-56),
    enabled: false,
  },
];

/** Price position vs competitor, derived from the same observations the
 * competitor screens use so the dashboard cannot disagree with them. */
const competitorPosition = (() => {
  const gapBySku = new Map<string, number>();
  for (const observation of COMPETITOR_PRICES) {
    const product = PRODUCTS.find((p) => p.id === observation.skuId);
    if (!product || !observation.listedPrice) continue;
    gapBySku.set(
      observation.skuId,
      (product.currentPrice - observation.listedPrice) / observation.listedPrice,
    );
  }
  let lower = 0;
  let equal = 0;
  let higher = 0;
  for (const gap of gapBySku.values()) {
    if (gap < -0.02) lower += 1;
    else if (gap > 0.02) higher += 1;
    else equal += 1;
  }
  return [
    { bucket: 'Thấp hơn', count: lower },
    { bucket: 'Tương đương', count: equal },
    { bucket: 'Cao hơn', count: higher },
  ];
})();

export const DASHBOARD: DashboardSummary = {
  revenue: 4_286_500_000,
  grossProfit: 812_400_000,
  margin: 0.1895,
  // Every KPI that also appears in a table is computed from that table.
  skusBelowFloor: RECOMMENDATIONS.filter((r) => r.recommendedPrice < r.floorPrice).length,
  lowStockCount: INVENTORY.filter((i) => i.onHandQty - i.reservedQty <= i.reorderPoint).length,
  pendingApprovals: RECOMMENDATIONS.filter((r) => r.status === 'PENDING_APPROVAL').length,
  revenueTrend: Array.from({ length: 14 }, (_, i) => {
    const day = new Date(now - (13 - i) * 86_400_000);
    const revenue = 240_000_000 + ((i * 17) % 7) * 12_500_000;
    return {
      date: day.toISOString().slice(0, 10),
      revenue,
      profit: Math.round(revenue * (0.17 + (i % 3) * 0.01)),
    };
  }),
  profitByChannel: CHANNELS.map((c, i) => ({
    channel: c.name,
    profit: Math.round(180_000_000 * (1 - i * 0.12)),
  })),
  priceVsCompetitor: competitorPosition,
};