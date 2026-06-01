import AgentCard, { type AgentCardData } from './AgentCard'
import MaterialIcon from './MaterialIcon'

const agents: AgentCardData[] = [
  {
    name: 'AuthAgent',
    version: 'v2.1.0',
    type: 'Core',
    rating: '4.8',
    icon: 'shield',
    tone: 'amber',
    description:
      'Handles all user authentication patterns across Clerk, NextAuth v5, and Supabase Auth',
    sources: ['clerk.com/docs', 'next-auth.js.org', 'supabase.com/auth'],
    synced: 'Synced 2h ago',
    installs: '12.4k',
  },
  {
    name: 'PaymentAgent',
    version: 'v1.4.0',
    type: 'Core',
    rating: '4.7',
    icon: 'credit_card',
    tone: 'green',
    description:
      'Payment processing and billing with Stripe, Razorpay, subscriptions, and checkout flows',
    sources: ['stripe.com/docs', '@stripe/stripe-js', 'razorpay.com'],
    synced: 'Synced 1h ago',
    installs: '9.8k',
  },
  {
    name: 'DBAgent',
    version: 'v3.0.1',
    type: 'Core',
    rating: '4.9',
    icon: 'database',
    tone: 'blue',
    description:
      'Database schema design and ORM with Prisma, Drizzle, and PostgreSQL best practices',
    sources: ['prisma.io/docs', 'drizzle.team', 'postgresql.org'],
    synced: 'Synced 3h ago',
    installs: '15.2k',
  },
  {
    name: 'FrontendAgent',
    version: 'v2.2.0',
    type: 'Core',
    rating: '4.6',
    icon: 'view_quilt',
    tone: 'violet',
    description:
      'React and Next.js UI state management with TanStack Query, Zustand, and Tailwind CSS',
    sources: ['nextjs.org/blog', 'tanstack.com', 'tailwindcss.com'],
    synced: 'Synced 2h ago',
    installs: '11.5k',
  },
  {
    name: 'DeployAgent',
    version: 'v1.1.0',
    type: 'Core',
    rating: '4.5',
    icon: 'cloud',
    tone: 'sky',
    description:
      'Deployment, CI/CD, and Dockerization with Vercel, Railway, and Docker best practices',
    sources: ['vercel.com/changelog', 'railway.app', 'docker.com'],
    synced: 'Synced 4h ago',
    installs: '7.3k',
  },
  {
    name: 'SupabaseAuthExpert',
    version: 'v1.0.3',
    type: 'Community',
    rating: '4.4',
    icon: 'lock',
    tone: 'green',
    description:
      'Supabase Auth and Row-Level Security specialist for secure database access patterns',
    sources: ['supabase.com/auth', 'supabase.com/rls'],
    synced: 'Synced 5h ago',
    installs: '3.2k',
  },
  {
    name: 'RazorpayIndiaAgent',
    version: 'v1.2.0',
    type: 'Community',
    rating: '4.6',
    icon: 'payments',
    tone: 'blue',
    description:
      'Indian payments and RBI compliance specialist for UPI, net banking, and local methods',
    sources: ['razorpay.com/docs', 'razorpay.com/webhooks'],
    synced: 'Synced 6h ago',
    installs: '2.1k',
  },
  {
    name: 'TestingAgent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.3',
    icon: 'science',
    tone: 'rose',
    description:
      'Unit and integration testing with Vitest, Testing Library, and Playwright E2E patterns',
    sources: ['vitest.dev', 'testing-library.com', 'playwright.dev'],
    synced: 'Synced 8h ago',
    installs: '5.6k',
  },
]

function AgentGrid() {
  return (
    <section className="agent-section">
      <div className="agent-section__header">
        <h2>Popular Agents</h2>
        <a href="#">
          View all <MaterialIcon name="arrow_forward" />
        </a>
      </div>

      <div className="agent-grid">
        {agents.map((agent) => (
          <AgentCard agent={agent} key={agent.name} />
        ))}
      </div>

      <div className="market-pagination">
        <span>Showing 8 of 24 agents</span>
        <button type="button">Load more agents</button>
      </div>
    </section>
  )
}

export default AgentGrid
