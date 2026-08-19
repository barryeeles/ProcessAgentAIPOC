import { useEffect, useState } from 'react'
import { api, type DeliveryResponse, type Release, type UnassignedCapability } from '../../api/client'
import { RAGTable } from '../RAGTable/RAGTable'
import { RAGDot } from '../RAGTable/RAGDot'
import { Sparkline } from '../RAGTable/Sparkline'
import type { RAGRowData } from '../RAGTable/RAGRow'

function toRowData(r: Release): RAGRowData {
  const s = r.snapshot ?? {}
  return {
    key: r.release_name,
    title: r.description ?? r.release_name,
    status: r.status ?? undefined,
    reported_rag: s.reported_rag ?? null,
    health_rag: s.health_rag ?? null,
    overall_score: s.overall_score ?? null,
    dq_score: s.dq_score ?? null,
    flow_score: s.flow_score ?? null,
    kpi_score: s.kpi_score ?? null,
    blocked_count: s.blocked_count ?? null,
    low_confidence: s.low_confidence ?? null,
    sparkline: r.sparkline,
  }
}

const SEV_CLASS: Record<string, string> = {
  HIGH: 'badge-R', MEDIUM: 'badge-A', WARNING: 'badge-U',
}

function UnassignedCapRow({
  cap,
  onSelect,
}: {
  cap: UnassignedCapability
  onSelect?: (capKey: string) => void
}) {
  const s = cap.snapshot
  const score = s.overall_score != null ? s.overall_score.toFixed(1) : '—'

  return (
    <tr
      style={{ cursor: onSelect ? 'pointer' : 'default' }}
      onClick={() => onSelect?.(cap.cap_key)}
    >
      <td style={{ fontFamily: 'monospace', fontSize: 11 }}>{cap.cap_key}</td>
      <td style={{ fontSize: 13 }}>{cap.title}</td>
      <td style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{cap.status}</td>
      <td style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
        {cap.delivery_increment ?? '—'}
      </td>
      <td style={{ textAlign: 'center' }}>
        <RAGDot rag={s.reported_rag ?? null} size={10} />
      </td>
      <td style={{ textAlign: 'right', fontWeight: 600, fontSize: 13 }}>{score}</td>
      <td>
        <Sparkline dots={cap.sparkline} />
      </td>
      <td>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {cap.dq_defects.map((d, i) => (
            <span
              key={i}
              className={`badge ${SEV_CLASS[d.severity] ?? 'badge-U'}`}
              style={{ fontSize: 9 }}
              title={d.description}
            >
              {d.rule_set}
            </span>
          ))}
        </div>
      </td>
    </tr>
  )
}

interface Props {
  epicKey: string
  week?: string
  onSelectRelease: (releaseName: string) => void
  onSelectCapability?: (capKey: string) => void
}

export function DeliveryManagerView({ epicKey, week, onSelectRelease, onSelectCapability }: Props) {
  const [data, setData] = useState<DeliveryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setData(null)
    setError(null)
    api.delivery(epicKey, week).then(setData).catch((e: Error) => setError(e.message))
  }, [epicKey, week])

  if (error) return <div className="state-error">{error}</div>
  if (!data) return <div className="state-loading">Loading releases for {epicKey}…</div>

  const rows = data.releases.map(toRowData)
  const unassigned = data.unassigned_capabilities ?? []

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">{data.epic.title}</h2>
        <span className="section-count">{rows.length} releases · {epicKey}</span>
      </div>

      <RAGTable
        rows={rows}
        showStatus
        onDrillDown={onSelectRelease}
        drillLabel="Capabilities"
        emptyMessage="No releases linked to this EPIC"
        hideKey
        hideSubScores
      />

      {unassigned.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <div className="section-header" style={{ marginBottom: 6 }}>
            <span className="section-title" style={{ fontSize: 14 }}>
              Capabilities without a Release
            </span>
            <span className="section-count">{unassigned.length}</span>
          </div>

          <div className="table-wrap surface">
            <table className="rag-table">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>DI</th>
                  <th style={{ textAlign: 'center' }}>RAG</th>
                  <th style={{ textAlign: 'right' }}>Score</th>
                  <th>Trend</th>
                  <th>DQ Flags</th>
                </tr>
              </thead>
              <tbody>
                {unassigned.map(cap => (
                  <UnassignedCapRow
                    key={cap.cap_key}
                    cap={cap}
                    onSelect={onSelectCapability}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
