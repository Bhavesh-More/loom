import MaterialIcon from './MaterialIcon'

type MarketplaceHeroProps = {
  searchTerm: string
  onSearchChange: (value: string) => void
}

function MarketplaceHero({ searchTerm, onSearchChange }: MarketplaceHeroProps) {
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
            value={searchTerm}
            onChange={(event) => onSearchChange(event.target.value)}
          />
        </label>
      </div>

    </section>
  )
}

export default MarketplaceHero
