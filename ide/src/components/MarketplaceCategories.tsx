import MaterialIcon from './MaterialIcon'

const categories = [
  {
    title: 'Authentication',
    description: 'OAuth, JWT, Sessions, MFA',
    tone: 'amber',
    icons: ['key', 'verified_user', 'admin_panel_settings'],
  },
  {
    title: 'Payments & Billing',
    description: 'Subscriptions, Checkout, Invoicing',
    tone: 'green',
    icons: ['credit_card', 'receipt_long', 'payments'],
  },
  {
    title: 'Database & ORM',
    description: 'Schema, Migrations, Queries',
    tone: 'blue',
    icons: ['database', 'table', 'storage'],
  },
  {
    title: 'Frontend & UI',
    description: 'Components, State, Styling',
    tone: 'violet',
    icons: ['view_quilt', 'data_object', 'palette'],
  },
]

function MarketplaceCategories() {
  return (
    <section className="market-categories" aria-label="Agent categories">
      {categories.map((category) => (
        <button
          className={`market-category market-category--${category.tone}`}
          type="button"
          key={category.title}
        >
          <span className="market-category__title">{category.title}</span>
          <span className="market-category__icons" aria-hidden="true">
            {category.icons.map((icon) => (
              <span key={icon}>
                <MaterialIcon name={icon} />
              </span>
            ))}
          </span>
          <span className="market-category__description">{category.description}</span>
        </button>
      ))}
    </section>
  )
}

export default MarketplaceCategories
