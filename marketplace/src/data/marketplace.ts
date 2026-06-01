import type {
  Agent,
  Category,
  Domain,
  HeroAgent,
  NavItem,
  Project,
  TeamSlot,
} from '../types/marketplace'

export const navItems: NavItem[] = [
  {
    id: 'nav-marketplace-link',
    label: 'Home',
    icon: 'lucide:store',
    page: 'home',
  },
  { id: 'nav-projects-link', label: 'Projects', icon: 'lucide:folder', page: 'projects' },
  { id: 'nav-teams-link', label: 'My Teams', icon: 'lucide:users' },
]

export const domains: Domain[] = [
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

export const categories: Category[] = [
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

export const heroAgents: HeroAgent[] = [
  {
    name: 'AuthAgent',
    stat: '4.8 Â· 12.4k',
    icon: 'lucide:shield',
    wrapClass: 'hero-mini-amber',
    iconClass: 'icon-amber-light',
  },
  {
    name: 'PaymentAgent',
    stat: '4.7 Â· 9.8k',
    icon: 'lucide:credit-card',
    wrapClass: 'hero-mini-emerald',
    iconClass: 'icon-emerald-light',
  },
  {
    name: 'DBAgent',
    stat: '4.9 Â· 15.2k',
    icon: 'lucide:database',
    wrapClass: 'hero-mini-blue',
    iconClass: 'icon-blue-light',
  },
]

export const agents: Agent[] = [
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

export const chips = [
  'All Agents',
  'Auth',
  'Payments',
  'Database',
  'Frontend',
  'DevOps',
  'Testing',
  'Community',
]

export const teamSlots: TeamSlot[] = [
  ['Auth', 'lucide:shield'],
  ['Payments', 'lucide:credit-card'],
  ['Database', 'lucide:database'],
  ['Frontend', 'lucide:layout'],
  ['Deploy', 'lucide:cloud'],
]

export const examples = [
  'SaaS app with auth and payments',
  'E-commerce with cart and checkout',
  'REST API with JWT and Postgres',
  'Admin dashboard with role-based access',
]

export const projects: Project[] = [
  {
    id: 'atlas-saas',
    name: 'Atlas SaaS Console',
    description:
      'Subscription workspace with secure onboarding, team roles, usage meters, and a billing-ready dashboard.',
    status: 'Live',
    statusClass: 'project-status live',
    accentClass: 'project-accent emerald-bg',
    updated: 'Updated 38m ago',
    stack: ['Clerk', 'Stripe', 'Postgres', 'React'],
    contributors: [
      {
        name: 'AuthAgent',
        icon: 'lucide:shield',
        iconClass: 'icon-amber',
        role: 'Login, sessions, MFA',
      },
      {
        name: 'PaymentAgent',
        icon: 'lucide:credit-card',
        iconClass: 'icon-emerald',
        role: 'Plans and checkout',
      },
      {
        name: 'FrontendAgent',
        icon: 'lucide:layout',
        iconClass: 'icon-violet',
        role: 'Dashboard UI',
      },
    ],
  },
  {
    id: 'commerce-pulse',
    name: 'Commerce Pulse',
    description:
      'Inventory storefront prototype with checkout recovery, payment webhooks, and operational reporting.',
    status: 'In Review',
    statusClass: 'project-status review',
    accentClass: 'project-accent blue-bg',
    updated: 'Updated 2h ago',
    stack: ['Razorpay', 'Drizzle', 'Tailwind', 'Playwright'],
    contributors: [
      {
        name: 'RazorpayIndiaAgent',
        icon: 'simple-icons:razorpay',
        iconClass: 'icon-blue',
        role: 'UPI and webhook flows',
      },
      {
        name: 'DBAgent',
        icon: 'lucide:database',
        iconClass: 'icon-blue',
        role: 'Orders schema',
      },
      {
        name: 'TestingAgent',
        icon: 'lucide:test-tube-2',
        iconClass: 'icon-rose',
        role: 'Checkout regression tests',
      },
    ],
  },
  {
    id: 'ops-board',
    name: 'Ops Board',
    description:
      'Internal admin surface for role-based approvals, deployment notes, audit events, and release readiness.',
    status: 'Draft',
    statusClass: 'project-status draft',
    accentClass: 'project-accent violet-bg',
    updated: 'Updated yesterday',
    stack: ['Supabase', 'Next.js', 'Vercel', 'Vitest'],
    contributors: [
      {
        name: 'SupabaseAuthExpert',
        icon: 'simple-icons:supabase',
        iconClass: 'icon-emerald',
        role: 'RLS policies',
      },
      {
        name: 'DeployAgent',
        icon: 'lucide:cloud',
        iconClass: 'icon-sky',
        role: 'Release pipeline',
      },
      {
        name: 'TestingAgent',
        icon: 'lucide:test-tube-2',
        iconClass: 'icon-rose',
        role: 'Unit coverage',
      },
    ],
  },
]
