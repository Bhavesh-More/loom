type MaterialIconProps = {
  name: string
  className?: string
  ariaLabel?: string
}

function MaterialIcon({ name, className = '', ariaLabel }: MaterialIconProps) {
  return (
    <span
      aria-hidden={ariaLabel ? undefined : true}
      aria-label={ariaLabel}
      className={`material-symbols-outlined ${className}`.trim()}
    >
      {name}
    </span>
  )
}

export default MaterialIcon
