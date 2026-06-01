import { createElement } from 'react'

type IconProps = {
  icon: string
  className?: string
}

function Icon({ icon, className = '' }: IconProps) {
  return createElement('iconify-icon', {
    'aria-hidden': 'true',
    class: className,
    icon,
  } as Record<string, string>)
}

export default Icon
