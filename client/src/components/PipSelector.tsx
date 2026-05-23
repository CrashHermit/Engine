interface PipSelectorProps {
  label: string
  value: number
  max?: number
  readonly?: boolean
  onChange?: (value: number) => void
}

export default function PipSelector({ label, value, max = 4, readonly = false, onChange }: PipSelectorProps) {
  return (
    <div className="pip-selector">
      <span className="pip-label">{label}</span>
      <div className="pip-bubbles">
        {Array.from({ length: max }).map((_, i) => (
          <button
            key={i}
            type="button"
            className={`pip ${i < value ? 'pip--filled' : 'pip--empty'}`}
            disabled={readonly}
            onClick={() => {
              if (readonly || !onChange) return
              // clicking an already-filled last pip deselects it
              onChange(i < value ? i : i + 1)
            }}
            aria-label={`${label} ${i + 1}`}
          />
        ))}
      </div>
    </div>
  )
}
