import type { RAG } from '../../api/client'

const SOLID: Record<string, string> = {
  G: 'var(--rag-green)',
  A: 'var(--rag-amber)',
  R: 'var(--rag-red)',
  U: 'var(--color-border)',
}

const LABEL: Record<string, string> = { G: 'Green', A: 'Amber', R: 'Red', U: 'Unknown' }

interface Props {
  rag: RAG | null | undefined
  size?: number
}

export function RAGDot({ rag, size = 13 }: Props) {
  const r = rag ?? 'U'
  return (
    <span
      style={{
        display: 'inline-block',
        width: size,
        height: size,
        borderRadius: '50%',
        background: SOLID[r] ?? SOLID.U,
        boxShadow: r !== 'U' ? `0 0 0 2px ${SOLID[r]}22` : undefined,
        verticalAlign: 'middle',
      }}
      title={LABEL[r] ?? 'Unknown'}
      aria-label={LABEL[r] ?? 'Unknown'}
    />
  )
}

export function RAGBadge({ rag }: { rag: RAG | null | undefined }) {
  const r = rag ?? 'U'
  return <span className={`badge badge-${r}`}>{LABEL[r]}</span>
}
