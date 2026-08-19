import type { RAG } from '../../api/client'
import { RAGDot } from './RAGDot'
import { Sparkline } from './Sparkline'

export interface RAGRowData {
  key: string
  title: string
  status?: string
  reported_rag?: RAG | null
  health_rag?: RAG | null
  overall_score?: number | null
  dq_score?: number | null
  flow_score?: number | null
  kpi_score?: number | null
  blocked_count?: number | null
  low_confidence?: number | null
  // optional cap counts so the UI can show how many caps contributed to each sub-score avg
  cap_total?: number | null
  flow_cap_count?: number | null
  kpi_cap_count?: number | null
  sparkline: (RAG | null)[]
  // when explicitly false, the drill-down button is hidden
  drillable?: boolean
}

interface Props {
  row: RAGRowData
  onDrillDown?: (key: string) => void
  drillLabel?: string
  dimmed?: boolean
  hideKey?: boolean
  hideSubScores?: boolean
}

function fmt(n: number | null | undefined) {
  if (n == null) return '—'
  return n.toFixed(1)
}

// Sub-score cell: shows the value and a tooltip when fewer caps contributed than the total.
function SubScore({
  value,
  count,
  total,
  label,
}: {
  value?: number | null
  count?: number | null
  total?: number | null
  label: string
}) {
  const partial = count != null && total != null && count < total
  const tip = partial
    ? `${label}: average of ${count}/${total} capabilities with data. The other ${total - count} cap(s) have no ${label} data and are scored on DQ alone — they still count in the EPIC overall.`
    : undefined
  return (
    <span
      className={`score-pill score-sub${partial ? ' score-partial' : ''}`}
      title={tip}
      style={{ cursor: partial ? 'help' : undefined }}
    >
      {fmt(value)}
      {partial && <span className="score-partial-badge">{count}/{total}</span>}
    </span>
  )
}

export function RAGRow({
  row,
  onDrillDown,
  drillLabel = 'Open',
  dimmed = false,
  hideKey = false,
  hideSubScores = false,
}: Props) {
  return (
    <tr style={{ opacity: dimmed ? 0.55 : 1 }}>
      {!hideKey && (
        <td className="col-key">
          <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{row.key}</span>
        </td>
      )}
      <td className="col-title">
        {row.title}
        {!!row.low_confidence && (
          <span className="lc-badge" title="Fewer than 50% of children contributing">LC</span>
        )}
      </td>
      {row.status !== undefined && (
        <td className="col-status">
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{row.status}</span>
        </td>
      )}
      <td className="col-rag">
        <RAGDot rag={row.reported_rag} size={13} />
      </td>
      <td className="col-score">
        <span className="score-pill">{fmt(row.overall_score)}</span>
      </td>
      {!hideSubScores && (
        <td className="col-dq">
          <span className="score-pill score-sub">{fmt(row.dq_score)}</span>
        </td>
      )}
      {!hideSubScores && (
        <td className="col-flow">
          <SubScore
            value={row.flow_score}
            count={row.flow_cap_count}
            total={row.cap_total}
            label="Flow"
          />
        </td>
      )}
      {!hideSubScores && (
        <td className="col-kpi">
          <SubScore
            value={row.kpi_score}
            count={row.kpi_cap_count}
            total={row.cap_total}
            label="KPI"
          />
        </td>
      )}
      <td className="col-blocked">
        {(row.blocked_count ?? 0) > 0 && (
          <span className="badge badge-R" style={{ fontSize: 10 }}>
            {row.blocked_count}
          </span>
        )}
      </td>
      <td className="col-trend">
        <Sparkline dots={row.sparkline} />
      </td>
      <td className="col-action">
        {onDrillDown && row.drillable !== false && (
          <button className="link-btn" onClick={() => onDrillDown(row.key)}>
            {drillLabel} →
          </button>
        )}
      </td>
    </tr>
  )
}
