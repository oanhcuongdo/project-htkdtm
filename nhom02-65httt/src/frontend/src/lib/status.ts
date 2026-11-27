import type { Tone } from '@/components/ui/primitives';
import type {
  ConnectionStatus,
  ExecutionStatus,
  MappingSyncStatus,
  RecommendationStatus,
  RuleStatus,
} from '@/types/domain';

export function recommendationStatus(status: RecommendationStatus): {
  label: string;
  tone: Tone;
} {
  const map: Record<RecommendationStatus, { label: string; tone: Tone }> = {
    DRAFT: { label: 'Nháp', tone: 'neutral' },
    PENDING_APPROVAL: { label: 'Chờ duyệt', tone: 'warning' },
    APPROVED: { label: 'Đã duyệt', tone: 'success' },
    EXECUTION_QUEUED: { label: 'Chờ thực thi', tone: 'info' },
    EXECUTED: { label: 'Đã thực thi', tone: 'success' },
    REJECTED: { label: 'Từ chối', tone: 'danger' },
    EXPIRED: { label: 'Hết hạn', tone: 'danger' },
    FAILED: { label: 'Thất bại', tone: 'danger' },
    CANCELLED: { label: 'Đã huỷ', tone: 'neutral' },
  };
  return map[status];
}

export function executionStatus(status: ExecutionStatus): {
  label: string;
  tone: Tone;
} {
  const map: Record<ExecutionStatus, { label: string; tone: Tone }> = {
    QUEUED: { label: 'Đang chờ', tone: 'neutral' },
    RUNNING: { label: 'Đang chạy', tone: 'info' },
    SUCCEEDED: { label: 'Thành công', tone: 'success' },
    PARTIAL: { label: 'Một phần', tone: 'warning' },
    FAILED: { label: 'Thất bại', tone: 'danger' },
    CANCELLED: { label: 'Đã huỷ', tone: 'neutral' },
  };
  return map[status];
}

export function ruleStatus(status: RuleStatus): { label: string; tone: Tone } {
  const map: Record<RuleStatus, { label: string; tone: Tone }> = {
    DRAFT: { label: 'Nháp', tone: 'neutral' },
    ACTIVE: { label: 'Đang hoạt động', tone: 'success' },
    PAUSED: { label: 'Tạm dừng', tone: 'warning' },
    ARCHIVED: { label: 'Đã lưu trữ', tone: 'neutral' },
  };
  return map[status];
}

export function connectionStatus(status: ConnectionStatus): {
  label: string;
  tone: Tone;
} {
  const map: Record<ConnectionStatus, { label: string; tone: Tone }> = {
    NOT_CONNECTED: { label: 'Chưa kết nối', tone: 'neutral' },
    DEMO: { label: 'Demo', tone: 'info' },
    CONNECTED: { label: 'Đã kết nối', tone: 'success' },
    ERROR: { label: 'Lỗi', tone: 'danger' },
    DISABLED: { label: 'Tắt', tone: 'neutral' },
  };
  return map[status];
}

export function dataQuality(quality: 'HIGH' | 'MEDIUM' | 'LOW'): {
  label: string;
  tone: Tone;
} {
  const map = {
    HIGH: { label: 'Cao', tone: 'success' as Tone },
    MEDIUM: { label: 'Trung bình', tone: 'warning' as Tone },
    LOW: { label: 'Thấp', tone: 'danger' as Tone },
  };
  return map[quality];
}

export function mappingSyncStatus(status: MappingSyncStatus): {
  label: string;
  tone: Tone;
} {
  const map: Record<MappingSyncStatus, { label: string; tone: Tone }> = {
    SYNCED: { label: 'Đã đồng bộ', tone: 'success' },
    PENDING: { label: 'Chờ đồng bộ', tone: 'warning' },
    ERROR: { label: 'Lỗi đồng bộ', tone: 'danger' },
    NOT_MAPPED: { label: 'Chưa map', tone: 'neutral' },
  };
  return map[status];
}

export function ruleTypeLabel(type: string): string {
  const map: Record<string, string> = {
    FLASH_SALE: 'Flash Sale',
    SKIMMING: 'Hớt váng',
    CLEARANCE: 'Xả kho',
    COMPETITOR_MATCH: 'Bám giá đối thủ',
    MARGIN_GUARD: 'Bảo vệ biên',
  };
  return map[type] ?? type;
}