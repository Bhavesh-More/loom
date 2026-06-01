const filters = [
  'All Agents',
  'Auth',
  'Payments',
  'Database',
  'Frontend',
  'DevOps',
  'Testing',
  'Community',
]

function MarketplaceFilterBar() {
  return (
    <div className="market-filter-bar">
      <div className="market-filter-bar__chips" aria-label="Marketplace filters">
        {filters.map((filter, index) => (
          <button
            className={`market-chip${index === 0 ? ' market-chip--active' : ''}`}
            type="button"
            key={filter}
          >
            {filter}
          </button>
        ))}
      </div>

      <label className="market-sort">
        <span>Sort</span>
        <select aria-label="Sort agents">
          <option>Most Installed</option>
          <option>Highest Rated</option>
          <option>Recently Synced</option>
          <option>Newest</option>
        </select>
      </label>
    </div>
  )
}

export default MarketplaceFilterBar
