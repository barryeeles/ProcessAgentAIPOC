import { useEffect, useState } from 'react'
import { api, type EpicRow, type SltResponse, type BlockedItemFull } from '../../api/client'
import { RAGTable } from '../RAGTable/RAGTable'
import type { RAGRowData } from '../RAGTable/RAGRow'
import { BlockedCallout } from '../BlockedCallout'

function toRowData(e: EpicRow): RAGRowData {
  return {
    key: e.epic_key,
    title: e.title,
    status: e.status,
    reported_rag: e.reported_rag,
    health_rag: e.health_rag,
    overall_score: e.overall_score,
    dq_score: e.avg_dq,
    flow_score: e.avg_flow,
    kpi_score: e.avg_kpi,
    blocked_count: e.blocked_count,
    low_confidence: e.low_confidence,
    cap_total: e.cap_total,
    flow_cap_count: e.flow_cap_count,
    kpi_cap_count: e.kpi_cap_count,
    sparkline: e.sparkline,
  }
}

interface Props {
  week?: string
  onSelectEpic: (epicKey: string, epicTitle: string) => void
}

export function SLTView({ week, onSelectEpic }: Props) {
  const [data, setData] = useState<SltResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [blocked, setBlocked] = useState<BlockedItemFull[]>([])

  useEffect(() => {
    setData(null)
    setError(null)
    api.slt(week).then(setData).catch((e: Error) => setError(e.message))
    api.blocked(week).then(r => setBlocked(r.items)).catch(() => setBlocked([]))
  }, [week])

  if (error) return <div className="state-error">{error}</div>
  if (!data) return <div className="state-loading">Loading SLT view…</div>

  const activeRows = data.epics.map(toRowData)
  const closedRows = data.recently_closed.map(toRowData)

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">Active EPICs</h2>
        <span className="section-count">{activeRows.length} EPICs · week {data.week}</span>
      </div>

      <BlockedCallout
        items={blocked.filter(b => b.stage === 'ESCALATE' || b.stage === 'PRIORITY')}
        showEpic
        showCap
      />

      <RAGTable
        rows={activeRows}
        showStatus
        onDrillDown={(key) => {
          const epic = data.epics.find(e => e.epic_key === key)
          onSelectEpic(key, epic?.title ?? key)
        }}
        drillLabel="Releases"
        emptyMessage="No active EPICs"
      />

      {closedRows.length > 0 && (
        <div className="closed-section">
          <div className="section-header">
            <h3 className="section-title">Recently Closed</h3>
            <span className="section-count">{closedRows.length} EPICs</span>
          </div>
          <RAGTable
            rows={closedRows}
            showStatus
            dimmed
            emptyMessage=""
          />
        </div>
      )}
    </div>
  )
}
