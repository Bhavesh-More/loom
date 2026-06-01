import type { ReactNode } from 'react'

type SidebarSectionProps = {
  title: string
  children: ReactNode
}

function SidebarSection({ title, children }: SidebarSectionProps) {
  return (
    <section className="sidebar-section">
      <h3>{title}</h3>
      <div className="section-stack">{children}</div>
    </section>
  )
}

export default SidebarSection
