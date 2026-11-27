/*
 * Domain types mirror ERP_Smart_Pricing_SPEC/DATABASE.md and API_SPEC.md.
 * These are UI-facing shapes. Backend remains the source of truth; enum
 * values and field names must match the spec exactly.
 */

export type Role =
  | 'ADMIN'
  | 'MANAGER'
  | 'PRICING_ANALYST'
  | 'INVENTORY_STAFF'
  | 'VIEWER';

export interface User {
  id: string;
  fullName: string;
  email: string;
  role: Role;
  isActive: boolean;
  lastLoginAt: string | null;
  createdAt: string;
}

export interface CostBreakdown {
  purchase: number;
  inbound: number;
  packaging: number;
  other: number;
}

export type ProductStatus = 'ACTIVE' | 'ARCHIVED';

export interface Category {
  id: string;
  name: string;
}

export interface Product {
  id: string;
  skuCode: string;
  name: string;
  variantName: string | null;
  categoryId: string;
  categoryName: string;
  unit: string;
  currentPrice: number;
  unitCost: number;
  costBreakdown: CostBreakdown;
  supplierId: string | null;
  supplierName: string | null;
  /** available = on_hand - reserved. null when the SKU has no inventory row. */
  availableQty: number | null;
  status: ProductStatus;
  updatedAt: string;
}

export interface Supplier {
  id: string;
  supplierCode: string;
  name: string;
  contactName: string | null;
  email: string | null;
  phone: string | null;
  skuCount: number;
  lastQuotedAt: string | null;
  status: 'ACTIVE' | 'INACTIVE';
}

export interface InventoryBalance {
  id: string;
  skuCode: string;
  productName: string;
  warehouseName: string;
  onHandQty: number;
  reservedQty: number;
  reorderPoint: number;
  updatedAt: string;
}

export type IntegrationMode = 'SIMULATED' | 'LIVE';
export type ConnectionStatus =
  | 'NOT_CONNECTED'
  | 'DEMO'
  | 'CONNECTED'
  | 'ERROR'
  | 'DISABLED';

export interface Channel {
  id: string;
  code: 'SHOPEE' | 'TIKTOK_SHOP' | 'LAZADA' | 'WEBSITE' | 'OTHER';
  name: string;
  integrationMode: IntegrationMode;
  connectionStatus: ConnectionStatus;
  isActive: boolean;
  listingCount: number;
  feeRate: number;
}

export interface Competitor {
  id: string;
  name: string;
  marketplaceCode: string;
  storeUrl: string;
  status: 'TRACKING' | 'PAUSED';
}

export type SourceType = 'MANUAL' | 'CSV' | 'API' | 'PUBLIC_PAGE' | 'DEMO';

export interface CompetitorPrice {
  id: string;
  skuId: string;
  skuCode: string;
  productName: string;
  competitorId: string;
  competitorName: string;
  marketplaceCode: string;
  listedPrice: number;
  effectivePrice: number | null;
  sourceType: SourceType;
  sourceName: string;
  observedAt: string;
  confidence: number;
  isOutlier: boolean;
}

export type RecommendationStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'EXECUTION_QUEUED'
  | 'EXECUTED'
  | 'REJECTED'
  | 'EXPIRED'
  | 'FAILED'
  | 'CANCELLED';

export type AlgorithmType = 'RULE_BASED' | 'ML_ASSISTED';

export interface ExplanationFactor {
  key: string;
  label: string;
  value: string;
  /** How the UI should render `value`; defaults to raw text. */
  format?: 'money' | 'percent' | 'number';
  impact: 'raises_floor' | 'anchors_price' | 'lowers_price' | 'neutral';
}

export interface Explanation {
  summary: string;
  factors: ExplanationFactor[];
  constraints: {
    floorPassed: boolean;
    maxChangePassed: boolean;
    competitorFresh: boolean;
  };
  dataQuality: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface Recommendation {
  id: string;
  skuId: string;
  skuCode: string;
  productName: string;
  channelId: string;
  channelName: string;
  status: RecommendationStatus;
  currentPrice: number;
  floorPrice: number;
  recommendedPrice: number;
  expectedProfitPerUnit: number;
  expectedMargin: number;
  /** Input snapshot: values the engine actually used (AI_PRICING §10). */
  unitCost: number;
  channelFeeRate: number;
  competitorMedian: number | null;
  targetMargin: number;
  dataQuality: 'HIGH' | 'MEDIUM' | 'LOW';
  algorithmType: AlgorithmType;
  algorithmVersion: string;
  explanation: Explanation;
  createdBy: string;
  createdAt: string;
  expiresAt: string;
}

export type RuleType =
  | 'FLASH_SALE'
  | 'SKIMMING'
  | 'CLEARANCE'
  | 'COMPETITOR_MATCH'
  | 'MARGIN_GUARD';

export type RuleStatus = 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'ARCHIVED';

export interface PricingRule {
  id: string;
  name: string;
  ruleType: RuleType;
  priority: number;
  scopeLabel: string;
  minMargin: number;
  maxPriceChangePct: number;
  approvalRequired: boolean;
  status: RuleStatus;
  startsAt: string;
  endsAt: string | null;
}

export type ExecutionStatus =
  | 'QUEUED'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'PARTIAL'
  | 'FAILED'
  | 'CANCELLED';

export interface ExecutionRun {
  id: string;
  skuCode: string;
  channelName: string;
  mode: IntegrationMode;
  requestedPrice: number;
  previousPrice: number;
  status: ExecutionStatus;
  attempts: number;
  errorCode: string | null;
  idempotencyKey: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuditLog {
  id: string;
  actor: string;
  action: string;
  resourceType: string;
  reason: string | null;
  requestId: string;
  beforeSummary: string | null;
  afterSummary: string | null;
  createdAt: string;
}

export type MappingSyncStatus = 'SYNCED' | 'PENDING' | 'ERROR' | 'NOT_MAPPED';

export interface ChannelListing {
  id: string;
  skuId: string;
  skuCode: string;
  productName: string;
  channelId: string;
  channelName: string;
  externalListingId: string;
  externalSku: string;
  currentPrice: number;
  syncStatus: MappingSyncStatus;
  lastSyncedAt: string | null;
}

export type FeeComponentType = 'PERCENT' | 'FIXED';

export interface ChannelFeeComponent {
  name: string;
  type: FeeComponentType;
  value: number;
  verified: boolean;
}

export interface ChannelFee {
  channelId: string;
  channelName: string;
  /** Sum of fixed-rate components, matches Channel.feeRate. */
  totalRate: number;
  effectiveFrom: string;
  source: string;
  components: ChannelFeeComponent[];
}

export type PricingJobStatus = 'QUEUED' | 'COMPLETED' | 'PARTIAL' | 'FAILED';

export interface PricingJob {
  id: string;
  channelName: string;
  objective: 'PROFIT' | 'COMPETITIVE' | 'CLEAR_STOCK';
  mode: AlgorithmType;
  targetMargin: number;
  skuCount: number;
  resultCount: number;
  noSafePriceCount: number;
  status: PricingJobStatus;
  createdAt: string;
}

export interface PricingSchedule {
  id: string;
  name: string;
  ruleName: string;
  cronLabel: string;
  mode: IntegrationMode;
  nextRunAt: string | null;
  enabled: boolean;
}

export interface DashboardSummary {
  revenue: number;
  grossProfit: number;
  margin: number;
  skusBelowFloor: number;
  lowStockCount: number;
  pendingApprovals: number;
  revenueTrend: { date: string; revenue: number; profit: number }[];
  profitByChannel: { channel: string; profit: number }[];
  priceVsCompetitor: { bucket: string; count: number }[];
}

export interface PageMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface Paged<T> {
  data: T[];
  meta: PageMeta;
}

export interface ApiError {
  code: string;
  message: string;
  details?: { field: string; message: string }[];
}