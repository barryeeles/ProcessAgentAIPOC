import { useEffect, useState } from 'react'
import { api, type Metadata } from './api/client'
import { SLTView } from './components/views/SLTView'
import { DeliveryManagerView } from './components/views/DeliveryManagerView'
import { ReleaseManagerView } from './components/views/ReleaseManagerView'
import { FileUpload } from './components/FileUpload'
import { CapabilityPanel } from './components/CapabilityPanel'
import { TransparencyPanel } from './components/TransparencyPanel'
import { CleanupChecklist } from './components/CleanupChecklist'
import './index.css'

// ── Navigation state ─────────────────────────────────────────────────────
type View =
  | { type: 'slt' }
  | { type: 'delivery'; epicKey: string; epicTitle?: string }
  | { type: 'release'; releaseName: string; epicKey: string; epicTitle?: string }
  | { type: 'checklist' }
  | { type: 'upload' }

function App() {
  const [view, setView] = useState<View>({ type: 'slt' })
  const [selectedWeek, setSelectedWeek] = useState<string | undefined>(undefined)
  const [metadata, setMetadata] = useState<Metadata | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [openCapKey, setOpenCapKey] = useState<string | null>(null)
  const [showTransparency, setShowTransparency] = useState(false)

  useEffect(() => {
    api.metadata().then(setMetadata).catch(() => null)
  }, [refreshKey])

  function handleUploaded() {
    // Reload metadata after a successful upload so the week selector updates
    setRefreshKey(k => k + 1)
    setView({ type: 'slt' })
  }

  function navSlt() {
    setView({ type: 'slt' })
  }

  function navDelivery(epicKey: string, epicTitle?: string) {
    setView({ type: 'delivery', epicKey, epicTitle })
  }

  function navRelease(releaseName: string, epicKey: string, epicTitle?: string) {
    setView({ type: 'release', releaseName, epicKey, epicTitle })
  }

  // ── Breadcrumb ──────────────────────────────────────────────────────────
  function Breadcrumb() {
    if (view.type === 'slt' || view.type === 'upload' || view.type === 'checklist') return null
    return (
      <nav className="breadcrumb">
        <button className="link-btn" onClick={navSlt}>SLT</button>
        {(view.type === 'delivery' || view.type === 'release') && (
          <>
            <span className="breadcrumb-sep">›</span>
            {view.type === 'release' ? (
              <button className="link-btn"
                onClick={() => navDelivery(view.epicKey, view.epicTitle)}>
                {view.epicTitle ?? view.epicKey}
              </button>
            ) : (
              <span className="breadcrumb-current">{view.epicTitle ?? view.epicKey}</span>
            )}
          </>
        )}
        {view.type === 'release' && (
          <>
            <span className="breadcrumb-sep">›</span>
            <span className="breadcrumb-current">{view.releaseName}</span>
          </>
        )}
      </nav>
    )
  }

  return (
    <div className="layout">
      {/* ── Top bar ── */}
      <header className="topbar">
        <button
          className="topbar-title"
          style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', padding: 0 }}
          onClick={navSlt}
        >
          Process Evaluation Agent
        </button>
        <span className="topbar-spacer" />

        {/* Week selector */}
        {metadata && metadata.available_weeks.length > 0 && (
          <select
            value={selectedWeek ?? metadata.available_weeks[0]}
            onChange={e => setSelectedWeek(e.target.value || undefined)}
            style={{
              background: 'rgba(255,255,255,.15)',
              border: '1px solid rgba(255,255,255,.3)',
              color: '#fff',
              borderRadius: 4,
              padding: '4px 8px',
              fontSize: 13,
            }}
          >
            {metadata.available_weeks.map(w => (
              <option key={w} value={w} style={{ background: '#333', color: '#fff' }}>{w}</option>
            ))}
          </select>
        )}

        <button
          className="btn"
          style={{ background: 'rgba(255,255,255,.15)', color: '#fff', border: '1px solid rgba(255,255,255,.3)' }}
          onClick={() => setView({ type: 'checklist' })}
        >
          Checklist
        </button>
        <button
          className="btn"
          style={{ background: 'rgba(255,255,255,.15)', color: '#fff', border: '1px solid rgba(255,255,255,.3)' }}
          onClick={() => setShowTransparency(t => !t)}
        >
          ℹ Scope
        </button>
        <button
          className="btn"
          style={{ background: 'rgba(255,255,255,.15)', color: '#fff', border: '1px solid rgba(255,255,255,.3)' }}
          onClick={() => setView({ type: 'upload' })}
        >
          Upload
        </button>
      </header>

      {/* ── Main ── */}
      <main className="main-content">
        <Breadcrumb />

        {view.type === 'upload' && (
          <>
            <div className="section-header">
              <h2 className="section-title">Upload Weekly Data</h2>
            </div>
            <FileUpload onUploaded={handleUploaded} />
          </>
        )}

        {view.type === 'slt' && (
          <SLTView
            week={selectedWeek}
            onSelectEpic={(key, title) => navDelivery(key, title)}
          />
        )}

        {view.type === 'delivery' && (
          <DeliveryManagerView
            epicKey={view.epicKey}
            week={selectedWeek}
            onSelectRelease={(releaseName) =>
              navRelease(releaseName, view.epicKey, view.epicTitle)
            }
          />
        )}

        {view.type === 'release' && (
          <ReleaseManagerView
            releaseName={view.releaseName}
            week={selectedWeek}
            onSelectCapability={(capKey) => setOpenCapKey(capKey)}
          />
        )}

        {view.type === 'checklist' && (
          <CleanupChecklist week={selectedWeek} />
        )}
      </main>

      {/* Capability slide-over panel */}
      {openCapKey && (
        <CapabilityPanel
          capKey={openCapKey}
          week={selectedWeek}
          onClose={() => setOpenCapKey(null)}
        />
      )}

      {/* Transparency sidebar */}
      {showTransparency && (
        <TransparencyPanel
          metadata={metadata}
          onClose={() => setShowTransparency(false)}
        />
      )}
    </div>
  )
}

export default App
