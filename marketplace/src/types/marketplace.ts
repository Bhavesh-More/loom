export type AppPage = 'home' | 'projects'

export type NavItem = {
  id: string
  label: string
  icon: string
  page?: AppPage
}

export type Domain = {
  id: string
  label: string
  icon: string
  iconClass: string
  count: number
}

export type Category = {
  title: string
  description: string
  className: string
  icons: Array<{ icon: string; className: string }>
}

export type HeroAgent = {
  name: string
  stat: string
  icon: string
  wrapClass: string
  iconClass: string
}

export type Agent = {
  id: string
  name: string
  version: string
  type: 'Core' | 'Community'
  icon: string
  iconClass: string
  iconWrapClass: string
  rating: string
  description: string
  sources: string[]
  synced: string
  syncClass: string
  installs: string
}

export type TeamSlot = [label: string, icon: string]

export type ProjectContributor = {
  name: string
  icon: string
  iconClass: string
  role: string
}

export type Project = {
  id: string
  name: string
  description: string
  status: 'Live' | 'In Review' | 'Draft'
  statusClass: string
  accentClass: string
  updated: string
  stack: string[]
  contributors: ProjectContributor[]
}
