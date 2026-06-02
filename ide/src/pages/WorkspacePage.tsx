import PromptComposer from '../components/PromptComposer'
// import RateLimitBanner from '../components/RateLimitBanner'
import Sidebar, { type AppPage } from '../components/Sidebar'
import SuggestionGrid from '../components/SuggestionGrid'
import TopAppBar from '../components/TopAppBar'

type WorkspacePageProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
}

function WorkspacePage({ activePage, onNavigate }: WorkspacePageProps) {
  return (
    <div className="workspace-app">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />

      <main className="workspace-main">
        <TopAppBar />

        <div className="workspace-main__content">
          <h1>What should we build in L00m?</h1>

          <div className="workspace-main__controls">
            {/* <RateLimitBanner /> */}
            <PromptComposer />
          </div>

          <SuggestionGrid />
        </div>
      </main>
    </div>
  )
}

export default WorkspacePage
