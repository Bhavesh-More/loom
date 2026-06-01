import { chips } from '../../data/marketplace'

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

export default StickyFilters
