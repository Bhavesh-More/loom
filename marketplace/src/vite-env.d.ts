/// <reference types="vite/client" />

declare namespace JSX {
  interface IntrinsicElements {
    'iconify-icon': {
      icon: string
      class?: string
      className?: string
      'aria-hidden'?: string
    }
  }
}
