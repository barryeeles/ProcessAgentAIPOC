import { useEffect, useState } from 'react'
import { api, type Capability, type ReleaseResponse } from '../../api/client'
import { RAGTable } from '../RAGTable/RAGTable'
import type { RAGRowData } from '../RAGTable/RAGRow'

function toRowData(c: Capability): RAGRowData {
  const s = c.snapshot ?? {}
  return {
    key: c.cap_key,
    title: c.title,
    status: c.status,
    reported_rag: s.reported_rag ?? null,
    health_rag: s.health_rag ?? null,
    overall_score: s.overall_score ?? null,
    dq_score: s.dq_score ?? null,
    flow_score: s.flow_score ?? null,
    kpi_score: s.kpi_score ?? null,
    blocked_count: s.blocked_count ?? null,
    low_confidence: s.low_confidence ?? null,
    sparkline: c.sparkline,
  }
}

interface Props {
  releaseName: string
  week?: string
  onSelectCapability: (capKey: string) => void
}

export function ReleaseManagerView({ releaseName, week, onSelectCapability }: Props) {
  const [data, setData] = useState<ReleaseResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setData(null)
    setError(null)
    api.release(releaseName, week).then(setData).catch((e: Error) => setError(e.message))
  }, [releaseName, week])

  if (error) return <div className="state-error">{error}</div>
  if (!data) return <div className="state-loading">Loading capabilities for release…</div>

  const rows = data.capabilities.map(toRowData)
  const rel = data.release

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">{rel.release_name}</h2>
        <span className="section-count">
          {rows.length} capabilities
          {rel.release_date ? ` · due ${rel.release_date}` : ''}
        </span>
      </div>

      <RAGTable
        rows={rows}
        showStatus
        onDrillDown={onSelectCapability}
        drillLabel="Features"
        emptyMessage="No in-scope capabilities linked to this release"
      />
    </div>
  )
}
