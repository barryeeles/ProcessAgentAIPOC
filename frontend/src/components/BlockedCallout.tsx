import type { BlockedItem, BlockedItemFull } from '../api/client'

type AnyBlocked = BlockedItem | BlockedItemFull

interface Props {
  items: AnyBlocked[]
  showEpic?: boolean
  showCap?: boolean
}

const STAGE_STYLE: Record<string, { border: string; bg: string; badge: string }> = {
  ESCALATE: { border: 'var(--rag-red)',     bg: 'var(--rag-red-bg)',     badge: 'badge-R' },
  PRIORITY:  { border: '#b45309',           bg: '#fef3c7',               badge: 'badge-A' },
  WARNING:   { border: 'var(--rag-amber)',  bg: 'var(--rag-amber-bg)',   badge: 'badge-A' },
  FLAGGED:   { border: 'var(--rag-unknown)', bg: 'var(--rag-unknown-bg)', badge: 'badge-U' },
}

const STAGE_ORDER = ['ESCALATE', 'PRIORITY', 'WARNING', 'FLAGGED']

function isFullItem(item: AnyBlocked): item is BlockedItemFull {
  return 'cap_title' in item
}

export function BlockedCallout({ items, showEpic = false, showCap = true }: Props) {
  if (items.length === 0) return null

  const sorted = [...items].sort(
    (a, b) => STAGE_ORDER.indexOf(a.stage) - STAGE_ORDER.indexOf(b.stage)
  )

  return (
    <div style={{ marginBottom: 16 }}>
      {sorted.map((item) => {
        const style = STAGE_STYLE[item.stage] ?? STAGE_STYLE.FLAGGED
        const title = isFullItem(item) ? item.feature_title : item.title ?? item.feature_key
        const capLabel = isFullItem(item) ? item.cap_title : null
        const epicLabel = isFullItem(item) ? item.epic_title : null

        return (
          <div
            key={item.feature_key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '7px 12px',
              marginBottom: 4,
              borderLeft: `4px solid ${style.border}`,
              background: style.bg,
              borderRadius: '0 var(--radius) var(--radius) 0',
              fontSize: 13,
            }}
          >
            <span className={`badge ${style.badge}`} style={{ flexShrink: 0 }}>
              {item.stage}
            </span>
            <span style={{ fontFamily: 'monospace', fontSize: 11, flexShrink: 0, color: 'var(--color-text-muted)' }}>
              {item.feature_key}
            </span>
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {title}
            </span>
            {showCap && capLabel && (
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', flexShrink: 0 }}>
                {capLabel}
              </span>
            )}
            {showEpic && epicLabel && (
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', flexShrink: 0 }}>
                {epicLabel}
              </span>
            )}
            <span style={{ fontSize: 11, fontWeight: 600, flexShrink: 0 }}>
              {item.weeks_consecutive}w blocked
            </span>
            {item.di_band && (
              <span className="badge badge-U" style={{ fontSize: 9, flexShrink: 0 }}>
                {item.di_band}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
