import { useEffect, useState } from 'react'
import { api, type DeliveryResponse, type Release } from '../../api/client'
import { RAGTable } from '../RAGTable/RAGTable'
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

interface Props {
  epicKey: string
  week?: string
  onSelectRelease: (releaseName: string) => void
}

export function DeliveryManagerView({ epicKey, week, onSelectRelease }: Props) {
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
      />
    </div>
  )
}
