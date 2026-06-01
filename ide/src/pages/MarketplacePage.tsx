import AgentGrid from '../components/AgentGrid'
import MarketplaceCategories from '../components/MarketplaceCategories'
import MarketplaceFilterBar from '../components/MarketplaceFilterBar'
import MarketplaceHero from '../components/MarketplaceHero'
import Sidebar, { type AppPage } from '../components/Sidebar'

type MarketplacePageProps = {
  onNavigate: (page: AppPage) => void
}

function MarketplacePage({ onNavigate }: MarketplacePageProps) {
  return (
    <div className="workspace-app">
      <Sidebar activePage="marketplace" onNavigate={onNavigate} />

      <main className="marketplace-main">
        <MarketplaceHero />
        <MarketplaceCategories />
        <MarketplaceFilterBar />
        <AgentGrid />
      </main>
    </div>
  )
}

export default MarketplacePage
