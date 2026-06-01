import { createElement, useState, type ReactNode } from 'react'
import './App.css'

type NavItem = {
  id: string
  label: string
  icon: string
  active?: boolean
}

type Domain = {
  id: string
  label: string
  icon: string
  iconClass: string
  count: number
}

type Category = {
  title: string
  description: string
  className: string
  icons: Array<{ icon: string; className: string }>
}

type Agent = {
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

const navItems: NavItem[] = [
  { id: 'nav-home-link', label: 'Home', icon: 'lucide:home' },
  {
    id: 'nav-marketplace-link',
    label: 'Marketplace',
    icon: 'lucide:store',
    active: true,
  },
  { id: 'nav-projects-link', label: 'Projects', icon: 'lucide:folder' },
  { id: 'nav-teams-link', label: 'My Teams', icon: 'lucide:users' },
]

const domains: Domain[] = [
  {
    id: 'filter-auth-link',
    label: 'Authentication',
    icon: 'lucide:shield',
    iconClass: 'icon-amber',
    count: 3,
  },
  {
    id: 'filter-payments-link',
    label: 'Payments & Billing',
    icon: 'lucide:credit-card',
    iconClass: 'icon-emerald',
    count: 4,
  },
  {
    id: 'filter-database-link',
    label: 'Database & ORM',
    icon: 'lucide:database',
    iconClass: 'icon-blue',
    count: 3,
  },
  {
    id: 'filter-frontend-link',
    label: 'Frontend & UI',
    icon: 'lucide:layout',
    iconClass: 'icon-violet',
    count: 4,
  },
  {
    id: 'filter-devops-link',
    label: 'DevOps & Deployment',
    icon: 'lucide:cloud',
    iconClass: 'icon-sky',
    count: 3,
  },
  {
    id: 'filter-testing-link',
    label: 'Testing & QA',
    icon: 'lucide:test-tube-2',
    iconClass: 'icon-rose',
    count: 2,
  },
  {
    id: 'filter-community-link',
    label: 'Community Picks',
    icon: 'lucide:sparkles',
    iconClass: 'icon-orange',
    count: 7,
  },
]

const categories: Category[] = [
  {
    title: 'Authentication',
    description: 'OAuth, JWT, Sessions, MFA',
    className: 'category-card category-amber',
    icons: [
      { icon: 'simple-icons:clerk', className: 'icon-violet' },
      { icon: 'simple-icons:supabase', className: 'icon-emerald' },
      { icon: 'simple-icons:auth0', className: 'icon-orange' },
    ],
  },
  {
    title: 'Payments & Billing',
    description: 'Subscriptions, Checkout, Invoicing',
    className: 'category-card category-emerald',
    icons: [
      { icon: 'simple-icons:stripe', className: 'icon-violet' },
      { icon: 'simple-icons:razorpay', className: 'icon-blue' },
      { icon: 'lucide:receipt', className: 'icon-slate' },
    ],
  },
  {
    title: 'Database & ORM',
    description: 'Schema, Migrations, Queries',
    className: 'category-card category-blue',
    icons: [
      { icon: 'simple-icons:prisma', className: 'icon-black' },
      { icon: 'simple-icons:postgresql', className: 'icon-blue' },
      { icon: 'lucide:database', className: 'icon-emerald' },
    ],
  },
  {
    title: 'Frontend & UI',
    description: 'Components, State, Styling',
    className: 'category-card category-violet',
    icons: [
      { icon: 'simple-icons:react', className: 'icon-cyan' },
      { icon: 'simple-icons:nextdotjs', className: 'icon-black' },
      { icon: 'simple-icons:tailwindcss', className: 'icon-cyan' },
    ],
  },
]

const heroAgents = [
  {
    name: 'AuthAgent',
    stat: '4.8 · 12.4k',
    icon: 'lucide:shield',
    wrapClass: 'hero-mini-amber',
    iconClass: 'icon-amber-light',
  },
  {
    name: 'PaymentAgent',
    stat: '4.7 · 9.8k',
    icon: 'lucide:credit-card',
    wrapClass: 'hero-mini-emerald',
    iconClass: 'icon-emerald-light',
  },
  {
    name: 'DBAgent',
    stat: '4.9 · 15.2k',
    icon: 'lucide:database',
    wrapClass: 'hero-mini-blue',
    iconClass: 'icon-blue-light',
  },
]

const agents: Agent[] = [
  {
    id: 'auth',
    name: 'AuthAgent',
    version: 'v2.1.0',
    type: 'Core',
    icon: 'lucide:shield',
    iconClass: 'icon-amber',
    iconWrapClass: 'agent-icon amber-bg',
    rating: '4.8',
    description:
      'Handles all user authentication patterns across Clerk, NextAuth v5, and Supabase Auth',
    sources: ['clerk.com/docs', 'next-auth.js.org', 'supabase.com/auth'],
    synced: 'Synced 2h ago',
    syncClass: 'icon-emerald',
    installs: '12.4k installs',
  },
  {
    id: 'payment',
    name: 'PaymentAgent',
    version: 'v1.4.0',
    type: 'Core',
    icon: 'lucide:credit-card',
    iconClass: 'icon-emerald',
    iconWrapClass: 'agent-icon emerald-bg',
    rating: '4.7',
    description:
      'Payment processing & billing with Stripe, Razorpay, subscriptions, and checkout flows',
    sources: ['stripe.com/docs', '@stripe/stripe-js', 'razorpay.com'],
    synced: 'Synced 1h ago',
    syncClass: 'icon-emerald',
    installs: '9.8k installs',
  },
  {
    id: 'db',
    name: 'DBAgent',
    version: 'v3.0.1',
    type: 'Core',
    icon: 'lucide:database',
    iconClass: 'icon-blue',
    iconWrapClass: 'agent-icon blue-bg',
    rating: '4.9',
    description:
      'Database schema design & ORM with Prisma, Drizzle, and PostgreSQL best practices',
    sources: ['prisma.io/docs', 'drizzle.team', 'postgresql.org'],
    synced: 'Synced 3h ago',
    syncClass: 'icon-emerald',
    installs: '15.2k installs',
  },
  {
    id: 'frontend',
    name: 'FrontendAgent',
    version: 'v2.2.0',
    type: 'Core',
    icon: 'lucide:layout',
    iconClass: 'icon-violet',
    iconWrapClass: 'agent-icon violet-bg',
    rating: '4.6',
    description:
      'React/Next.js UI & state management with TanStack Query, Zustand, and Tailwind CSS',
    sources: ['nextjs.org/blog', 'tanstack.com', 'tailwindcss.com'],
    synced: 'Synced 2h ago',
    syncClass: 'icon-emerald',
    installs: '11.5k installs',
  },
  {
    id: 'deploy',
    name: 'DeployAgent',
    version: 'v1.1.0',
    type: 'Core',
    icon: 'lucide:cloud',
    iconClass: 'icon-sky',
    iconWrapClass: 'agent-icon sky-bg',
    rating: '4.5',
    description:
      'Deployment, CI/CD & Dockerization with Vercel, Railway, and Docker best practices',
    sources: ['vercel.com/changelog', 'railway.app', 'docker.com'],
    synced: 'Synced 4h ago',
    syncClass: 'icon-amber',
    installs: '7.3k installs',
  },
  {
    id: 'supabase',
    name: 'SupabaseAuthExpert',
    version: 'v1.0.3',
    type: 'Community',
    icon: 'simple-icons:supabase',
    iconClass: 'icon-emerald',
    iconWrapClass: 'agent-icon emerald-bg',
    rating: '4.4',
    description:
      'Supabase Auth & Row-Level Security specialist for secure database access patterns',
    sources: ['supabase.com/auth', 'supabase.com/rls'],
    synced: 'Synced 5h ago',
    syncClass: 'icon-amber',
    installs: '3.2k installs',
  },
  {
    id: 'razorpay',
    name: 'RazorpayIndiaAgent',
    version: 'v1.2.0',
    type: 'Community',
    icon: 'simple-icons:razorpay',
    iconClass: 'icon-blue',
    iconWrapClass: 'agent-icon blue-bg',
    rating: '4.6',
    description:
      'Indian payments & RBI compliance specialist for UPI, net banking, and local methods',
    sources: ['razorpay.com/docs', 'razorpay.com/webhooks'],
    synced: 'Synced 6h ago',
    syncClass: 'icon-orange',
    installs: '2.1k installs',
  },
  {
    id: 'testing',
    name: 'TestingAgent',
    version: 'v1.0.0',
    type: 'Core',
    icon: 'lucide:test-tube-2',
    iconClass: 'icon-rose',
    iconWrapClass: 'agent-icon rose-bg',
    rating: '4.3',
    description:
      'Unit & integration testing with Vitest, Testing Library, and Playwright E2E patterns',
    sources: ['vitest.dev', 'testing-library.com', 'playwright.dev'],
    synced: 'Synced 8h ago',
    syncClass: 'icon-orange',
    installs: '5.6k installs',
  },
]

const chips = [
  'All Agents',
  'Auth',
  'Payments',
  'Database',
  'Frontend',
  'DevOps',
  'Testing',
  'Community',
]

const teamSlots = [
  ['Auth', 'lucide:shield'],
  ['Payments', 'lucide:credit-card'],
  ['Database', 'lucide:database'],
  ['Frontend', 'lucide:layout'],
  ['Deploy', 'lucide:cloud'],
]

const examples = [
  'SaaS app with auth and payments',
  'E-commerce with cart and checkout',
  'REST API with JWT and Postgres',
  'Admin dashboard with role-based access',
]

function Icon({ icon, className = '' }: { icon: string; className?: string }) {
  return createElement('iconify-icon', {
    'aria-hidden': 'true',
    class: className,
    icon,
  } as Record<string, string>)
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="brand-mark">
          <Icon icon="lucide:layers" className="brand-icon" />
        </div>
        <span className="font-display brand-name">Loom</span>
      </div>

      <nav className="sidebar-nav" aria-label="Primary">
        <div className="nav-group primary-nav">
          {navItems.map((item) => (
            <a
              className={`nav-link${item.active ? ' active' : ''}`}
              href="#"
              id={item.id}
              key={item.id}
            >
              <Icon icon={item.icon} className="nav-icon" />
              {item.label}
            </a>
          ))}
        </div>

        <SidebarSection title="Browse by Domain">
          <div className="domain-list">
            {domains.map((domain) => (
              <a className="domain-link" href="#" id={domain.id} key={domain.id}>
                <span>
                  <Icon icon={domain.icon} className={domain.iconClass} />
                  {domain.label}
                </span>
                <strong>{domain.count}</strong>
              </a>
            ))}
          </div>
        </SidebarSection>

        <SidebarSection title="Filter by Type">
          <label className="check-row">
            <input defaultChecked type="checkbox" />
            <span>Core Agents</span>
          </label>
          <label className="check-row">
            <input defaultChecked type="checkbox" />
            <span>Community Agents</span>
          </label>
        </SidebarSection>

        <SidebarSection title="Filter by Freshness">
          <label className="check-row">
            <input name="freshness" type="radio" />
            <span>Synced within 6 hours</span>
          </label>
          <label className="check-row">
            <input name="freshness" type="radio" />
            <span>Synced within 24 hours</span>
          </label>
          <label className="check-row">
            <input defaultChecked name="freshness" type="radio" />
            <span>Any</span>
          </label>
        </SidebarSection>

        <SidebarSection title="Filter by Rating">
          <label className="check-row">
            <input name="rating" type="radio" />
            <span className="rating-label">
              4.5+ <Icon icon="lucide:star" className="icon-amber tiny-icon" />
            </span>
          </label>
          <label className="check-row">
            <input name="rating" type="radio" />
            <span className="rating-label">
              4.0+ <Icon icon="lucide:star" className="icon-amber tiny-icon" />
            </span>
          </label>
          <label className="check-row">
            <input defaultChecked name="rating" type="radio" />
            <span>Any</span>
          </label>
        </SidebarSection>
      </nav>

      <div className="user-card">
        <div className="avatar">JD</div>
        <div className="user-copy">
          <p>John Doe</p>
          <span>Pro Plan</span>
        </div>
        <button aria-label="Settings" className="settings-button" type="button">
          <Icon icon="lucide:settings" />
        </button>
      </div>
    </aside>
  )
}

function SidebarSection({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  return (
    <section className="sidebar-section">
      <h3>{title}</h3>
      <div className="section-stack">{children}</div>
    </section>
  )
}

function Hero() {
  return (
    <section className="hero-section">
      <div className="hero-content">
        <div className="hero-copy">
          <h1>Discover the world's top AI coding agents</h1>
          <p>
            Build faster with pre-trained agents that know your stack. Fresh
            knowledge, zero hallucinations.
          </p>
          <label className="search-box">
            <Icon icon="lucide:search" />
            <input
              placeholder="Search agents by name, specialty, or library..."
              type="text"
            />
          </label>
        </div>
      </div>

      <div className="floating-agents" aria-hidden="true">
        {heroAgents.map((agent) => (
          <div className="floating-agent-card" key={agent.name}>
            <div className="floating-agent-row">
              <div className={`floating-agent-icon ${agent.wrapClass}`}>
                <Icon icon={agent.icon} className={agent.iconClass} />
              </div>
              <div>
                <p>{agent.name}</p>
                <span>
                  {agent.stat.split(' · ')[0]}
                  <Icon icon="lucide:star" className="icon-amber" />·{' '}
                  {agent.stat.split(' · ')[1]}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function CategoryCards() {
  return (
    <section className="category-section">
      <div className="category-grid">
        {categories.map((category) => (
          <article className={category.className} key={category.title}>
            <h3>{category.title}</h3>
            <div className="category-icons">
              {category.icons.map((item) => (
                <span className="category-icon" key={`${category.title}-${item.icon}`}>
                  <Icon icon={item.icon} className={item.className} />
                </span>
              ))}
            </div>
            <p>{category.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function StickyFilters() {
  return (
    <div className="sticky-filters">
      <div className="chip-row">
        {chips.map((chip, index) => (
          <button
            className={`filter-chip${index === 0 ? ' active' : ''}`}
            key={chip}
            type="button"
          >
            {chip}
          </button>
        ))}
      </div>
      <select aria-label="Sort agents" defaultValue="Most Installed">
        <option>Most Installed</option>
        <option>Highest Rated</option>
        <option>Recently Synced</option>
        <option>Newest</option>
      </select>
    </div>
  )
}

function AgentGrid() {
  return (
    <section className="agent-section">
      <div className="section-heading">
        <h2>Popular Agents</h2>
        <a href="#" id="view-all-link">
          View all
          <Icon icon="lucide:arrow-right" />
        </a>
      </div>

      <div className="agent-grid">
        {agents.map((agent) => (
          <AgentCard agent={agent} key={agent.id} />
        ))}
      </div>

      <div className="pagination">
        <span>Showing 8 of 24 agents</span>
        <button type="button">Load more agents</button>
      </div>
    </section>
  )
}

function AgentCard({ agent }: { agent: Agent }) {
  return (
    <article className={`agent-card${agent.type === 'Community' ? ' community' : ''}`}>
      <div className="agent-card-top">
        <div className="agent-title-row">
          <div className={agent.iconWrapClass}>
            <Icon icon={agent.icon} className={agent.iconClass} />
          </div>
          <div>
            <div className="agent-name-row">
              <h3>{agent.name}</h3>
              <span>{agent.version}</span>
            </div>
            <strong className={agent.type === 'Core' ? 'core-badge' : 'community-badge'}>
              {agent.type}
            </strong>
          </div>
        </div>
        <div className="agent-rating">
          <Icon icon="lucide:star" className="icon-amber" />
          <span>{agent.rating}</span>
        </div>
      </div>

      <p className="agent-description">{agent.description}</p>

      <div className="source-list">
        {agent.sources.map((source) => (
          <span className="source-tag" key={`${agent.id}-${source}`}>
            {source}
          </span>
        ))}
      </div>

      <div className="agent-meta">
        <span>
          <Icon icon="lucide:refresh-cw" className={agent.syncClass} />
          {agent.synced}
        </span>
        <span>
          <Icon icon="lucide:download" />
          {agent.installs}
        </span>
      </div>

      <div className="agent-actions">
        <button type="button">Add to Team</button>
        <a href="#" id={`${agent.id}-details-link`}>
          Details
        </a>
      </div>
    </article>
  )
}

function TeamBuilderModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean
  onClose: () => void
}) {
  if (!isOpen) return null

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        aria-labelledby="team-builder-title"
        aria-modal="true"
        className="team-modal"
        role="dialog"
      >
        <div className="modal-header">
          <div className="modal-title-row">
            <div className="modal-mark">
              <Icon icon="lucide:sparkles" />
            </div>
            <div>
              <h2 id="team-builder-title">AI Team Builder</h2>
              <p>Describe what you're building</p>
            </div>
          </div>
          <button aria-label="Close modal" className="close-button" onClick={onClose} type="button">
            <Icon icon="lucide:x" />
          </button>
        </div>

        <div className="modal-content">
          <textarea placeholder="e.g. I want to build a SaaS app with user login, Stripe subscriptions, a PostgreSQL database, and a React dashboard" />

          <div className="example-chips">
            {examples.map((example) => (
              <button key={example} type="button">
                {example}
              </button>
            ))}
          </div>

          <button className="recommend-button" type="button">
            <Icon icon="lucide:wand-2" />
            Recommend my team
          </button>

          <div className="modal-divider">
            <span></span>
            <p>Or build manually</p>
            <span></span>
          </div>

          <label className="modal-search">
            <Icon icon="lucide:search" />
            <input placeholder="Search agents to add..." type="text" />
          </label>

          <div className="team-slots">
            <p>Team Slots</p>
            <div>
              {teamSlots.map(([label, icon]) => (
                <span className="team-slot" key={label}>
                  <Icon icon={icon} />
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

function App() {
  const [isTeamBuilderOpen, setIsTeamBuilderOpen] = useState(false)

  return (
    <div className="marketplace-app">
      <Sidebar />

      <main className="main-content">
        <Hero />
        <CategoryCards />
        <StickyFilters />
        <AgentGrid />
      </main>

      <button
        className="build-team-button"
        onClick={() => setIsTeamBuilderOpen(true)}
        type="button"
      >
        <Icon icon="lucide:sparkles" />
        <span>Build Team with AI</span>
      </button>

      <TeamBuilderModal
        isOpen={isTeamBuilderOpen}
        onClose={() => setIsTeamBuilderOpen(false)}
      />
    </div>
  )
}

export default App
