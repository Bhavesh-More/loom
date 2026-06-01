import MaterialIcon from './MaterialIcon'

const suggestions = [
  {
    title: 'Refactor Logic',
    description: 'Analyze complexity in the auth module',
    icon: 'code',
    tone: 'blue',
  },
  {
    title: 'System Design',
    description: 'Plan the database schema for projects',
    icon: 'architecture',
    tone: 'green',
  },
  {
    title: 'Debug Session',
    description: 'Trace the race condition in telemetry',
    icon: 'bug_report',
    tone: 'red',
  },
]

function SuggestionGrid() {
  return (
    <section className="suggestions" aria-label="Suggested prompts">
      {suggestions.map((suggestion) => (
        <button className="suggestion-card" type="button" key={suggestion.title}>
          <MaterialIcon
            className={`suggestion-card__icon suggestion-card__icon--${suggestion.tone}`}
            name={suggestion.icon}
          />
          <span className="suggestion-card__title">{suggestion.title}</span>
          <span className="suggestion-card__description">{suggestion.description}</span>
        </button>
      ))}
    </section>
  )
}

export default SuggestionGrid
