import {
  MARKETPLACE_FILTERS,
  MARKETPLACE_SORT_OPTIONS,
  type MarketplaceFilter,
  type MarketplaceSort,
} from '../lib/marketplace'

type MarketplaceFilterBarProps = {
  activeFilter: MarketplaceFilter
  sortOption: MarketplaceSort
  onFilterChange: (filter: MarketplaceFilter) => void
  onSortChange: (sort: MarketplaceSort) => void
}

function MarketplaceFilterBar({
  activeFilter,
  sortOption,
  onFilterChange,
  onSortChange,
}: MarketplaceFilterBarProps) {
  return (
    <div className="market-filter-bar">
      <div className="market-filter-bar__chips" aria-label="Marketplace filters">
        {MARKETPLACE_FILTERS.map((filter) => (
          <button
            className={`market-chip${filter === activeFilter ? ' market-chip--active' : ''}`}
            type="button"
            key={filter}
            onClick={() => onFilterChange(filter)}
          >
            {filter}
          </button>
        ))}
      </div>

      <label className="market-sort">
        <span>Sort</span>
        <select
          aria-label="Sort agents"
          value={sortOption}
          onChange={(event) => onSortChange(event.target.value as MarketplaceSort)}
        >
          {MARKETPLACE_SORT_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}

export default MarketplaceFilterBar
