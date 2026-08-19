import { useEffect, useState } from 'react'
import { api, type CapabilityDetail, type FeatureDetail } from '../api/client'
import { RAGDot } from './RAGTable/RAGDot'
import { Sparkline } from './RAGTable/Sparkline'
import { BlockedCallout } from './BlockedCallout'

interface Props {
  capKey: string
  week?: string
  onClose: () => void
}

const SEV_CLASS: Record<string, string> = {
  HIGH: 'badge-R', MEDIUM: 'badge-A', WARNING: 'badge-U',
}

function fmt(n: number | null | undefined) {
  return n == null ? '—' : n.toFixed(1)
}

function FeatureRow({ f, week }: { f: CapabilityDetail['features'][0]; week?: string }) {
  const [detail, setDetail] = useState<FeatureDetail | null>(null)
  const [open, setOpen] = useState(false)

  function toggle() {
    if (!open && !detail) {
      api.feature(f.feature_key, week).then(setDetail).catch(() => {})
    }
    setOpen(o => !o)
  }

  const statusColor = f.status === 'Done' ? 'var(--rag-green)'
    : f.status === 'Cancelled' ? 'var(--color-text-muted)'
    : f.status === 'Blocked' ? 'var(--rag-red)'
    : 'var(--color-text)'

  return (
    <>
      <tr
        style={{ cursor: 'pointer' }}
        onClick={toggle}
      >
        <td style={{ fontFamily: 'monospace', fontSize: 11 }}>{f.feature_key}</td>
        <td style={{ fontSize: 12 }}>{f.title}</td>
        <td style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 11, color: statusColor }}>{f.status}</span>
        </td>
        <td style={{ textAlign: 'center', fontSize: 11, color: 'var(--color-text-muted)' }}>
          {f.delivery_increment ?? '—'}
        </td>
        <td style={{ textAlign: 'center' }}>
          {f.previously_blocked === 1 && (
            <span className="badge badge-R" style={{ fontSize: 9 }}>BLK</span>
          )}
        </td>
        <td style={{ textAlign: 'center', fontSize: 11, color: 'var(--color-primary)' }}>
          {open ? '▲' : '▼'}
        </td>
      </tr>
      {open && detail && (
        <tr>
          <td colSpan={6} style={{ background: 'var(--color-bg)', padding: '10px 16px' }}>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', fontSize: 12 }}>
              {Object.entries({
                'Full Cycle Time': detail.kpis.full_cycle_time,
                'Delivery Predictability': detail.kpis.delivery_predictability,
                'Delivery Cycle Time': detail.kpis.delivery_cycle_time,
              }).map(([label, kpi]) => (
                <div key={label} className="surface" style={{ padding: '8px 12px', minWidth: 140 }}>
                  <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>{label}</div>
                  {kpi ? (
                    <>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <RAGDot rag={kpi.rag} size={10} />
                        <span style={{ fontWeight: 600 }}>{kpi.elapsed_days}d</span>
                        <span style={{ color: 'var(--color-text-muted)' }}>/ {kpi.sla_days}d SLA</span>
                      </div>
                      {!kpi.is_complete && (
                        <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 2 }}>in progress</div>
                      )}
                    </>
                  ) : (
                    <span style={{ color: 'var(--color-text-muted)' }}>—</span>
                  )}
                </div>
              ))}
            </div>
            {detail.blocked && (
              <div style={{ marginTop: 8 }}>
                <BlockedCallout items={[{ ...detail.blocked, title: f.title }]} showCap={false} />
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

export function CapabilityPanel({ capKey, week, onClose }: Props) {
  const [data, setData] = useState<CapabilityDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setData(null)
    setError(null)
    api.capability(capKey, week).then(setData).catch((e: Error) => setError(e.message))
  }, [capKey, week])

  const snap = data?.snapshot
  const cap = data?.capability

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)', zIndex: 100,
        }}
      />

      {/* Panel */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, width: 540,
        background: 'var(--color-surface)', zIndex: 101,
        boxShadow: '-4px 0 20px rgba(0,0,0,0.15)',
        display: 'flex', flexDirection: 'column',
        overflowY: 'auto',
      }}>
        {/* Header */}
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid var(--color-border)',
          display: 'flex', alignItems: 'flex-start', gap: 12,
          position: 'sticky', top: 0, background: 'var(--color-surface)', zIndex: 1,
        }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--color-text-muted)' }}>
              {capKey}
            </div>
            <div style={{ fontWeight: 700, fontSize: 15, marginTop: 2 }}>
              {cap?.title ?? capKey}
            </div>
            {cap && (
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>
                {cap.status}
                {cap.delivery_increment && ` · ${cap.delivery_increment}`}
              </div>
            )}
          </div>
          <button
            className="btn btn-ghost"
            onClick={onClose}
            style={{ flexShrink: 0, padding: '4px 10px', fontSize: 13 }}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '16px 18px', flex: 1 }}>
          {error && <div className="state-error">{error}</div>}
          {!data && !error && <div className="state-loading">Loading…</div>}

          {data && (
            <>
              {/* Score summary */}
              {snap && (
                <div className="surface" style={{ padding: '10px 14px', marginBottom: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                    <RAGDot rag={snap.reported_rag ?? null} size={16} />
                    <span style={{ fontWeight: 700, fontSize: 16 }}>
                      {fmt(snap.overall_score)}
                    </span>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>overall</span>
                    <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--color-text-muted)' }}>
                      DQ <strong>{fmt(snap.dq_score)}</strong>
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                      Flow <strong>{fmt(snap.flow_score)}</strong>
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                      KPI <strong>{fmt(snap.kpi_score)}</strong>
                    </span>
                  </div>
                  <div style={{ marginTop: 10 }}>
                    <Sparkline dots={data.sparkline} />
                  </div>
                </div>
              )}

              {/* Blocked */}
              {data.blocked_features.length > 0 && (
                <div style={{ marginBottom: 14 }}>
                  <div className="section-header" style={{ marginBottom: 6 }}>
                    <span className="section-title" style={{ fontSize: 13 }}>Blocked Features</span>
                  </div>
                  <BlockedCallout items={data.blocked_features} showCap={false} />
                </div>
              )}

              {/* Features */}
              <div style={{ marginBottom: 14 }}>
                <div className="section-header" style={{ marginBottom: 6 }}>
                  <span className="section-title" style={{ fontSize: 13 }}>Features</span>
                  <span className="section-count">{data.features.length}</span>
                </div>
                <div className="table-wrap surface">
                  <table className="rag-table">
                    <thead>
                      <tr>
                        <th>Key</th>
                        <th>Title</th>
                        <th style={{ textAlign: 'center' }}>Status</th>
                        <th style={{ textAlign: 'center' }}>DI</th>
                        <th style={{ textAlign: 'center' }}>Blk</th>
                        <th style={{ textAlign: 'center' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.features.map(f => (
                        <FeatureRow key={f.feature_key} f={f} week={week} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* DQ Defects */}
              {data.dq_defects.length > 0 && (
                <div>
                  <div className="section-header" style={{ marginBottom: 6 }}>
                    <span className="section-title" style={{ fontSize: 13 }}>Data Quality Defects</span>
                    <span className="section-count">{data.dq_defects.length}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {data.dq_defects.map(d => (
                      <div
                        key={d.id}
                        className="surface"
                        style={{ padding: '8px 12px', fontSize: 12 }}
                      >
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                          <span className={`badge ${SEV_CLASS[d.severity] ?? 'badge-U'}`} style={{ fontSize: 10 }}>
                            {d.severity}
                          </span>
                          <span style={{ fontFamily: 'monospace', fontSize: 10, color: 'var(--color-text-muted)' }}>
                            {d.rule_set}
                          </span>
                        </div>
                        <div style={{ color: 'var(--color-text)' }}>{d.description}</div>
                        {d.required_action && (
                          <div style={{ marginTop: 4, color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                            → {d.required_action}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  )
}
