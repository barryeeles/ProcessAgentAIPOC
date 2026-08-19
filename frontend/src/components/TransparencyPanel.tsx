import { useEffect, useState } from 'react'
import { api, type Metadata, type ScopeSummary } from '../api/client'

interface Props {
  metadata: Metadata | null
  onClose: () => void
}

function StatRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13 }}>
      <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
      <span style={{ fontWeight: 600 }}>{value}</span>
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.6px',
      color: 'var(--color-text-muted)', marginTop: 18, marginBottom: 6,
    }}>
      {children}
    </div>
  )
}

export function TransparencyPanel({ metadata, onClose }: Props) {
  const [scope, setScope] = useState<ScopeSummary | null>(null)

  useEffect(() => {
    api.scopeSummary().then(setScope).catch(() => {})
  }, [])

  const latest = metadata?.latest
  const weeks = metadata?.available_weeks ?? []

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.25)', zIndex: 100 }}
      />

      {/* Drawer */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, width: 360,
        background: 'var(--color-surface)', zIndex: 101,
        boxShadow: '-4px 0 20px rgba(0,0,0,0.12)',
        overflowY: 'auto',
      }}>
        {/* Header */}
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid var(--color-border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          position: 'sticky', top: 0, background: 'var(--color-surface)', zIndex: 1,
        }}>
          <span style={{ fontWeight: 700, fontSize: 15 }}>Scope & Status</span>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding: '4px 10px', fontSize: 13 }}>
            ✕
          </button>
        </div>

        <div style={{ padding: '10px 18px 24px' }}>

          {/* Latest upload */}
          {latest && (
            <>
              <SectionTitle>Latest Upload</SectionTitle>
              <div className="surface" style={{ padding: '10px 14px' }}>
                <StatRow label="Week" value={latest.upload_week} />
                <StatRow label="Uploaded at" value={new Date(latest.uploaded_at).toLocaleString()} />
                <StatRow label="EPICs in scope" value={latest.epics_in_scope} />
                <StatRow label="Capabilities in scope" value={latest.capabilities_in_scope} />
                <StatRow label="Features in scope" value={latest.features_in_scope} />
              </div>
            </>
          )}

          {/* Scope counts */}
          {scope && (
            <>
              <SectionTitle>EPICs</SectionTitle>
              <div className="surface" style={{ padding: '10px 14px' }}>
                <StatRow label="Active" value={scope.epics.active} />
                <StatRow label="Recently closed" value={scope.epics.recently_closed} />
                <StatRow label="Historically excluded" value={scope.epics.historical_excluded} />
                <StatRow label="Out of scope" value={scope.epics.excluded} />
                <StatRow label="Total in DB" value={scope.epics.total} />
              </div>

              <SectionTitle>Capabilities</SectionTitle>
              <div className="surface" style={{ padding: '10px 14px' }}>
                <StatRow label="In scope" value={scope.capabilities.in_scope} />
                <StatRow label="Excluded" value={scope.capabilities.excluded} />
                <StatRow label="Total in DB" value={scope.capabilities.total} />
              </div>

              <SectionTitle>Features</SectionTitle>
              <div className="surface" style={{ padding: '10px 14px' }}>
                <StatRow label="In scope" value={scope.features.in_scope} />
                <StatRow label="Excluded" value={scope.features.excluded} />
                <StatRow label="Total in DB" value={scope.features.total} />
              </div>

              <SectionTitle>Scoring Engine</SectionTitle>
              <div className="surface" style={{ padding: '10px 14px' }}>
                <StatRow label="DQ defects (this week)" value={scope.dq_defects_total} />
                <StatRow label="Snapshots total" value={scope.snapshots_total} />
                <StatRow label="Feature transitions" value={scope.feature_transitions_total} />
              </div>
            </>
          )}

          {/* AI agents (Phase 5 placeholders) */}
          <SectionTitle>AI Agents</SectionTitle>
          <div className="surface" style={{ padding: '10px 14px' }}>
            {[
              { name: 'DQ Narrator', note: 'Haiku 4.5' },
              { name: 'Chat Agent', note: 'Sonnet 5' },
              { name: 'Email Drafter', note: 'Sonnet 5' },
            ].map(({ name, note }) => (
              <div
                key={name}
                style={{
                  display: 'flex', justifyContent: 'space-between',
                  padding: '4px 0', fontSize: 13,
                  borderBottom: '1px solid var(--color-border)',
                }}
              >
                <span>{name} <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>({note})</span></span>
                <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Not yet active</span>
              </div>
            ))}
          </div>

          {/* Available weeks */}
          {weeks.length > 0 && (
            <>
              <SectionTitle>Available Weeks ({weeks.length})</SectionTitle>
              <div className="surface" style={{ padding: '8px 14px', maxHeight: 160, overflowY: 'auto' }}>
                {weeks.map(w => (
                  <div key={w} style={{ fontSize: 12, padding: '2px 0', fontFamily: 'monospace' }}>{w}</div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}
