// Typed fetch wrappers for all backend endpoints.

export type RAG = 'G' | 'A' | 'R' | 'U'
export type DeliveryStatus = 'on_track' | 'at_risk' | 'late' | 'unassessed'

export interface Snapshot {
  overall_score: number | null
  health_rag: RAG | null
  reported_rag: RAG | null
  delivery_status: DeliveryStatus | null
  dq_score: number | null
  flow_score: number | null
  kpi_score: number | null
  children_total: number
  children_contributing: number
  low_confidence: number
  blocked_count: number
  high_risk_count: number
}

export interface EpicRow {
  epic_key: string
  title: string
  status: string
  // snapshot fields (null when no data yet)
  overall_score: number | null
  health_rag: RAG | null
  reported_rag: RAG | null
  delivery_status: DeliveryStatus | null
  children_total: number | null
  children_contributing: number | null
  low_confidence: number | null
  blocked_count: number | null
  high_risk_count: number | null
  avg_dq: number | null
  avg_flow: number | null
  avg_kpi: number | null
  // how many caps contributed to each sub-score average (SQL AVG ignores NULLs)
  cap_total: number | null
  flow_cap_count: number | null
  kpi_cap_count: number | null
  sparkline: (RAG | null)[]
}

export interface SltResponse {
  week: string | null
  epics: EpicRow[]
  recently_closed: EpicRow[]
}

export interface Release {
  release_name: string
  status: string | null
  start_date: string | null
  release_date: string | null
  progress: string | null
  description: string | null
  snapshot: Partial<Snapshot>
  sparkline: (RAG | null)[]
}

export interface UnassignedCapability {
  cap_key: string
  title: string
  status: string
  delivery_increment: string | null
  snapshot: Partial<Snapshot>
  sparkline: (RAG | null)[]
  dq_defects: Array<{ rule_set: string; severity: string; description: string }>
}

export interface DeliveryResponse {
  epic: { epic_key: string; title: string; status: string }
  week: string | null
  releases: Release[]
  unassigned_capabilities: UnassignedCapability[]
}

export interface Capability {
  cap_key: string
  epic_key: string
  title: string
  status: string
  delivery_increment: string | null
  target_start_date: string | null
  target_end_date: string | null
  art: string | null
  in_scope: number
  snapshot: Partial<Snapshot>
  sparkline: (RAG | null)[]
}

export interface ReleaseResponse {
  release: { release_name: string; status?: string | null; release_date?: string | null }
  week: string | null
  capabilities: Capability[]
}

export interface Feature {
  feature_key: string
  cap_key: string
  title: string
  status: string
  delivery_increment: string | null
  target_start_date: string | null
  target_end_date: string | null
  date_committed: string | null
  date_done: string | null
  created_date: string
  art: string | null
  in_scope: number
  previously_blocked: number
}

export interface KpiEntry {
  start_date: string
  end_date: string
  elapsed_days: number
  sla_days: number
  rag: RAG
  score: number
  is_complete: boolean
}

export interface FeatureKpis {
  full_cycle_time: KpiEntry | null
  delivery_predictability: KpiEntry | null
  delivery_cycle_time: KpiEntry | null
}

export interface BlockedItem {
  feature_key: string
  upload_week: string
  weeks_consecutive: number
  stage: 'FLAGGED' | 'WARNING' | 'PRIORITY' | 'ESCALATE'
  di_band: string | null
  penalty_pct: number | null
  title?: string
}

export interface DqDefect {
  id: number
  upload_week: string
  entity_key: string
  entity_type: string
  rule_set: string
  severity: 'HIGH' | 'MEDIUM' | 'WARNING'
  description: string
  scoring_attribution: string
  first_seen_week: string | null
  required_action: string | null
  narration: string | null
}

export interface Transition {
  id: number
  feature_key?: string
  epic_key?: string
  from_status: string | null
  to_status: string
  transition_date: string
  upload_week: string
}

export interface EpicDetail {
  epic: { epic_key: string; title: string; status: string; delivery_increment: string | null }
  week: string | null
  snapshot: Snapshot | null
  sparkline: (RAG | null)[]
  transitions: Transition[]
  releases: string[]
  blocked_features: (BlockedItem & { title: string; cap_key: string })[]
  dq_defect_count: number
}

export interface CapabilityDetail {
  capability: Capability
  week: string | null
  snapshot: Snapshot | null
  sparkline: (RAG | null)[]
  features: Feature[]
  blocked_features: (BlockedItem & { title: string })[]
  dq_defects: DqDefect[]
  releases: string[]
}

export interface FeatureDetail {
  feature: Feature
  week: string | null
  transitions: Transition[]
  kpis: FeatureKpis
  blocked: BlockedItem | null
  dq_defects: DqDefect[]
}

export interface BlockedItemFull extends BlockedItem {
  feature_title: string
  cap_key: string
  cap_title: string
  epic_key: string
  epic_title: string
}

export interface BlockedResponse {
  week: string | null
  items: BlockedItemFull[]
}

export interface ChecklistDefect {
  id: number
  upload_week: string
  entity_key: string
  entity_type: string
  rule_set: string
  severity: 'HIGH' | 'MEDIUM' | 'WARNING'
  description: string
  scoring_attribution: string
  first_seen_week: string | null
  required_action: string | null
  narration: string | null
}

export interface ChecklistSection {
  section: string
  title: string
  count: number
  defects: ChecklistDefect[]
}

export interface ChecklistResponse {
  week: string | null
  sections: ChecklistSection[]
  total: number
}

export interface ScopeSummary {
  epics: {
    total: number
    in_scope: number
    active: number
    historical_excluded: number
    recently_closed: number
    excluded: number
  }
  capabilities: { total: number; in_scope: number; excluded: number }
  features: { total: number; in_scope: number; excluded: number }
  feature_transitions_total: number
  dq_defects_total: number
  snapshots_total: number
}

export interface Metadata {
  available_weeks: string[]
  latest: {
    upload_week: string
    uploaded_at: string
    epics_in_scope: number
    capabilities_in_scope: number
    features_in_scope: number
  } | null
}

// ── Fetch helper ────────────────────────────────────────────────────────────

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${path}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ── API functions ───────────────────────────────────────────────────────────

export const api = {
  slt: (week?: string) =>
    get<SltResponse>(`/api/slt${week ? `?week=${week}` : ''}`),

  delivery: (epicKey: string, week?: string) =>
    get<DeliveryResponse>(`/api/delivery/${epicKey}${week ? `?week=${week}` : ''}`),

  release: (releaseName: string, week?: string) =>
    get<ReleaseResponse>(`/api/release/${encodeURIComponent(releaseName)}${week ? `?week=${week}` : ''}`),

  epic: (key: string, week?: string) =>
    get<EpicDetail>(`/api/epic/${key}${week ? `?week=${week}` : ''}`),

  capability: (key: string, week?: string) =>
    get<CapabilityDetail>(`/api/capability/${key}${week ? `?week=${week}` : ''}`),

  feature: (key: string, week?: string) =>
    get<FeatureDetail>(`/api/feature/${key}${week ? `?week=${week}` : ''}`),

  blocked: (week?: string) =>
    get<BlockedResponse>(`/api/blocked${week ? `?week=${week}` : ''}`),

  checklist: (week?: string, epicKey?: string) => {
    const params = new URLSearchParams()
    if (week) params.set('week', week)
    if (epicKey) params.set('epic_key', epicKey)
    const qs = params.toString()
    return get<ChecklistResponse>(`/api/checklist${qs ? `?${qs}` : ''}`)
  },

  checklistExportUrl: (week?: string) =>
    `/api/checklist/export${week ? `?week=${week}` : ''}`,

  scopeSummary: () => get<ScopeSummary>('/api/scope-summary'),

  metadata: () => get<Metadata>('/api/metadata'),

  upload: async (files: { main?: File; releases?: File }): Promise<unknown> => {
    const form = new FormData()
    if (files.main) form.append('main_file', files.main)
    if (files.releases) form.append('releases_file', files.releases)
    const res = await fetch('/api/upload', { method: 'POST', body: form })
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText)
      throw new Error(`Upload failed ${res.status}: ${text}`)
    }
    return res.json()
  },
}
