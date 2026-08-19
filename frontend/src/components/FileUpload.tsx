import { useRef, useState } from 'react'
import { api } from '../api/client'
import './FileUpload.css'

interface Props {
  onUploaded: () => void
}

export function FileUpload({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'done' | 'error'>('idle')
  const [message, setMessage] = useState<string | null>(null)
  const [main, setMain] = useState<File | null>(null)
  const [releases, setReleases] = useState<File | null>(null)
  const mainRef = useRef<HTMLInputElement>(null)
  const relRef = useRef<HTMLInputElement>(null)

  function classify(file: File): 'main' | 'releases' | null {
    const name = file.name.toLowerCase()
    if (name.includes('release')) return 'releases'
    if (name.endsWith('.xlsx')) return 'main'
    return null
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    for (const file of Array.from(e.dataTransfer.files)) {
      const kind = classify(file)
      if (kind === 'main') setMain(file)
      else if (kind === 'releases') setReleases(file)
    }
  }

  async function upload() {
    if (!main && !releases) return
    setStatus('uploading')
    setMessage(null)
    try {
      const result = await api.upload({ main: main ?? undefined, releases: releases ?? undefined }) as Record<string, unknown>
      const week = result.upload_week as string
      const snaps = result.snapshots_written as number
      setMessage(`Uploaded week ${week} — ${snaps} snapshots written.`)
      setStatus('done')
      setMain(null)
      setReleases(null)
      onUploaded()
    } catch (e: unknown) {
      setStatus('error')
      setMessage(e instanceof Error ? e.message : 'Upload failed')
    }
  }

  return (
    <div className="upload-panel surface">
      <div
        className={`drop-zone${dragging ? ' drop-zone--active' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => mainRef.current?.click()}
      >
        <span className="drop-icon">📂</span>
        <p>Drop <strong>EPIC.xlsx</strong> and/or <strong>EPIC Releases.xlsx</strong> here</p>
        <p className="drop-hint">or click to select files</p>
      </div>

      <input ref={mainRef} type="file" accept=".xlsx" style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; if (f) setMain(f) }} />
      <input ref={relRef} type="file" accept=".xlsx" style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; if (f) setReleases(f) }} />

      <div className="upload-files">
        <FileChip label="EPIC.xlsx" file={main} onClear={() => setMain(null)}
          onPick={() => mainRef.current?.click()} />
        <FileChip label="EPIC Releases.xlsx" file={releases} onClear={() => setReleases(null)}
          onPick={() => relRef.current?.click()} />
      </div>

      {message && (
        <p className={status === 'error' ? 'upload-msg upload-msg--error' : 'upload-msg upload-msg--ok'}>
          {message}
        </p>
      )}

      <button
        className="btn btn-primary"
        onClick={upload}
        disabled={(!main && !releases) || status === 'uploading'}
      >
        {status === 'uploading' ? 'Uploading…' : 'Upload & Score'}
      </button>
    </div>
  )
}

function FileChip({ label, file, onClear, onPick }: {
  label: string; file: File | null; onClear: () => void; onPick: () => void
}) {
  return (
    <div className={`file-chip${file ? ' file-chip--ready' : ''}`} onClick={file ? undefined : onPick}>
      {file ? (
        <>
          <span className="file-chip-name">{file.name}</span>
          <button className="file-chip-clear" onClick={e => { e.stopPropagation(); onClear() }}
            title="Remove">✕</button>
        </>
      ) : (
        <span className="file-chip-placeholder">{label}</span>
      )}
    </div>
  )
}
