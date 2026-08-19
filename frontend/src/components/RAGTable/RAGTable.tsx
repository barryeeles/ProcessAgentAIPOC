import { RAGRow, type RAGRowData } from './RAGRow'

interface Props {
  rows: RAGRowData[]
  onDrillDown?: (key: string) => void
  drillLabel?: string
  showStatus?: boolean
  dimmed?: boolean
  emptyMessage?: string
}

export function RAGTable({
  rows,
  onDrillDown,
  drillLabel,
  showStatus = false,
  dimmed = false,
  emptyMessage = 'No items',
}: Props) {
  if (rows.length === 0) {
    return <p className="state-empty">{emptyMessage}</p>
  }
  return (
    <div className="table-wrap surface">
      <table className="rag-table">
        <thead>
          <tr>
            <th className="col-key">Key</th>
            <th className="col-title">Title</th>
            {showStatus && <th className="col-status">Status</th>}
            <th className="col-rag">RAG</th>
            <th className="col-score">Score</th>
            <th className="col-dq">DQ</th>
            <th className="col-flow">Flow</th>
            <th className="col-kpi">KPI</th>
            <th className="col-blocked">Blocked</th>
            <th className="col-trend">Trend (11w)</th>
            <th className="col-action"></th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <RAGRow
              key={row.key}
              row={row}
              onDrillDown={onDrillDown}
              drillLabel={drillLabel}
              dimmed={dimmed}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
