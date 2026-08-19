import { useEffect, useState } from 'react'
import { api, type ChecklistResponse, type ChecklistSection } from '../api/client'

interface Props {
  week?: string
  epicKey?: string
}

const SEV_CLASS: Record<string, string> = {
  HIGH: 'badge-R', MEDIUM: 'badge-A', WARNING: 'badge-U',
}

function Section({ section, defaultOpen }: { section: ChecklistSection; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="surface" style={{ marginBottom: 12 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', background: 'none', border: 'none', cursor: 'pointer',
          padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 10,
          textAlign: 'left',
        }}
      >
        <span style={{ fontWeight: 700, fontSize: 14, flex: 1 }}>
          {section.section} — {section.title}
        </span>
        <span className={`badge ${section.count > 0 ? 'badge-R' : 'badge-U'}`} style={{ fontSize: 11 }}>
          {section.count}
        </span>
        <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{open ? '▲' : '▼'}</span>
      </button>

      {open && section.count > 0 && (
        <div style={{ borderTop: '1px solid var(--color-border)' }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ width: 80 }}>Severity</th>
                  <th style={{ width: 60 }}>Rule</th>
                  <th style={{ width: 80 }}>Type</th>
                  <th style={{ width: 110 }}>Entity</th>
                  <th>Description</th>
                  <th>Required Action</th>
                </tr>
              </thead>
              <tbody>
                {section.defects.map(d => (
                  <tr key={d.id}>
                    <td>
                      <span className={`badge ${SEV_CLASS[d.severity] ?? 'badge-U'}`} style={{ fontSize: 10 }}>
                        {d.severity}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{d.rule_set}</span>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{d.entity_type}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: 11 }}>{d.entity_key}</td>
                    <td style={{ fontSize: 12 }}>{d.description}</td>
                    <td style={{ fontSize: 12, color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                      {d.required_action ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {open && section.count === 0 && (
        <div style={{ padding: '10px 14px', fontSize: 13, color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)' }}>
          No defects in this section.
        </div>
      )}
    </div>
  )
}

export function CleanupChecklist({ week, epicKey }: Props) {
  const [data, setData] = useState<ChecklistResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setData(null)
    setError(null)
    api.checklist(week, epicKey).then(setData).catch((e: Error) => setError(e.message))
  }, [week, epicKey])

  if (error) return <div className="state-error">{error}</div>
  if (!data) return <div className="state-loading">Loading checklist…</div>

  return (
    <div>
      <div className="section-header" style={{ marginBottom: 16 }}>
        <h2 className="section-title">DQ Cleanup Checklist</h2>
        <span className="section-count">{data.total} defects · week {data.week}</span>
        <div style={{ marginLeft: 'auto' }}>
          <a
            href={api.checklistExportUrl(week)}
            className="btn btn-ghost"
            style={{ fontSize: 12 }}
            download
          >
            Export CSV
          </a>
        </div>
      </div>

      {data.sections.map((section, i) => (
        <Section key={section.section} section={section} defaultOpen={i === 0} />
      ))}
    </div>
  )
}
