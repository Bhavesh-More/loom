export const MARKETPLACE_FILTERS = [
  'All Agents',
  'API',
  'Data',
  'AI',
  'DevOps',
  'Security',
  'Testing',
] as const

export type MarketplaceFilter = (typeof MARKETPLACE_FILTERS)[number]

export const MARKETPLACE_SORT_OPTIONS = [
  'Most Installed',
  'Highest Rated',
  'Recently Synced',
  'Newest',
] as const

export type MarketplaceSort = (typeof MARKETPLACE_SORT_OPTIONS)[number]

export type AgentCategory = Exclude<MarketplaceFilter, 'All Agents'>
