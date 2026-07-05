const suggestions = [
  {
    title: "Refactor Logic",
    description: "Analyze complexity in the auth module",
    icon: "code",
    tone: "text-secondary",
  },
  {
    title: "System Design",
    description: "Plan the database schema for projects",
    icon: "architecture",
    tone: "text-tertiary-fixed-dim",
  },
  {
    title: "Debug Session",
    description: "Trace the race condition in telemetry",
    icon: "bug_report",
    tone: "text-error",
  },
];

function SuggestionGrid() {
  return (
    <section
      className="grid relative grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-12 w-full max-w-5xl px-4 opacity-40 hover:opacity-100 transition-opacity duration-500"
      aria-label="Suggested prompts"
    >
      {suggestions.map((suggestion) => (
        <button
          className="p-4 border border-outline-variant/20 rounded-xl hover:bg-surface-container-high cursor-pointer transition-all hover:-translate-y-0.5 text-left bg-surface-container-low/50"
          type="button"
          key={suggestion.title}
        >
          <span
            className={`material-symbols-outlined ${suggestion.tone} block mb-2 text-[20px]`}
          >
            {suggestion.icon}
          </span>
          <h3 className="font-title-md text-[14px] text-white font-medium mb-1">
            {suggestion.title}
          </h3>
          <p className="text-[12px] text-on-surface-variant leading-relaxed">
            {suggestion.description}
          </p>
        </button>
      ))}
    </section>
  );
}

export default SuggestionGrid;
