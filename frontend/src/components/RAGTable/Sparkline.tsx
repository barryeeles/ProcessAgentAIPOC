import type { RAG } from '../../api/client'
import './Sparkline.css'

interface Props {
  dots: (RAG | null)[]
}

const COLOR: Record<string, string> = {
  G: 'var(--rag-green)',
  A: 'var(--rag-amber)',
  R: 'var(--rag-red)',
}

const LABEL: Record<string, string> = {
  G: 'Green',
  A: 'Amber',
  R: 'Red',
}

export function Sparkline({ dots }: Props) {
  return (
    <span className="sparkline" aria-label="RAG trend">
      {dots.map((rag, i) => (
        <span
          key={i}
          className="sparkline-dot"
          style={{ background: rag ? COLOR[rag] : 'var(--rag-unknown-bg)' }}
          title={rag ? `Week -${dots.length - 1 - i}: ${LABEL[rag]}` : 'No data'}
        />
      ))}
    </span>
  )
}
