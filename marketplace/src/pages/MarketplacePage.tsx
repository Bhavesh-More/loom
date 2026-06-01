import AgentGrid from '../components/marketplace/AgentGrid'
import CategoryCards from '../components/marketplace/CategoryCards'
import Hero from '../components/marketplace/Hero'
import StickyFilters from '../components/marketplace/StickyFilters'

function MarketplacePage() {
  return (
    <>
      <Hero />
      <CategoryCards />
      <StickyFilters />
      <AgentGrid />
    </>
  )
}

export default MarketplacePage
