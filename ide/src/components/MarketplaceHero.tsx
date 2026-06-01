import MaterialIcon from './MaterialIcon'

function MarketplaceHero() {
  return (
    <section className="market-hero">
      <div className="market-hero__copy">
        <h1>Discover the world's top AI coding agents</h1>
        <p>
          Build faster with pre-trained agents that know your stack. Fresh
          knowledge, zero hallucinations.
        </p>

        <label className="market-search">
          <MaterialIcon name="search" />
          <input
            type="search"
            placeholder="Search agents by name, specialty, or library..."
          />
        </label>

        <button className="market-hero__cta" type="button">
          <MaterialIcon name="add" />
          <span>Create Agent</span>
        </button>
      </div>
    </section>
  )
}

export default MarketplaceHero
