import { useState } from 'react'

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
  const [activeFilter, setActiveFilter] = useState(filters[0])

  return (
    <div className="market-filter-bar">
      <div className="market-filter-bar__chips" aria-label="Marketplace filters">
        {filters.map((filter) => (
          <button
            className={`market-chip${filter === activeFilter ? ' market-chip--active' : ''}`}
            type="button"
            key={filter}
            onClick={() => setActiveFilter(filter)}
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
