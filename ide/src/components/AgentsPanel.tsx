import { type AgentData } from "../lib/agents";

type AgentsPanelProps = {
  downloadedAgents: AgentData[];
  onUninstallClick: (agent: AgentData) => void;
  onClose: () => void;
  onNavigateToMarketplace: (agentId?: string | null) => void;
};

export default function AgentsPanel({
  downloadedAgents,
  onUninstallClick,
  onClose,
  onNavigateToMarketplace,
}: AgentsPanelProps) {
  return (
    <div className="w-full h-full bg-[#151515] rounded-3xl border border-[#2A2A2A] shadow-2xl overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between px-8 py-7 border-b border-[#262626]">
        <div>
          <h2 className="text-2xl font-semibold text-white">Attached Agents</h2>

          <p className="text-sm text-[#9A9A9A] mt-2 max-w-xl">
            Manage the agents installed in your workspace. Click an agent to
            view its marketplace page or remove it from your account.
          </p>
        </div>

        <button
          onClick={onClose}
          className="w-10 h-10 rounded-xl hover:bg-[#242424] flex items-center justify-center transition cursor-pointer"
        >
          <span className="material-symbols-outlined text-white">close</span>
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-8 py-8">
        {downloadedAgents.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center">
            <div className="w-20 h-20 rounded-2xl bg-[#1B1B1B] border border-[#2A2A2A] flex items-center justify-center">
              <span className="material-symbols-outlined text-[36px] text-[#777]">
                smart_toy
              </span>
            </div>

            <h3 className="text-white text-xl font-semibold mt-6">
              No Agents Installed
            </h3>

            <p className="text-[#999] text-sm mt-2 text-center max-w-md">
              Install agents from the marketplace to extend your workspace with
              specialized capabilities.
            </p>

            <button
              onClick={() => onNavigateToMarketplace(null)}
              className="mt-8 px-6 py-3 rounded-xl bg-primary text-on-primary font-medium hover:opacity-90 transition"
            >
              Browse Marketplace
            </button>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h3 className="text-white font-semibold">Installed Agents</h3>

                <p className="text-xs text-[#8B8B8B] mt-1">
                  {downloadedAgents.length} installed
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-6">
              {downloadedAgents.map((agent) => (
                <div
                  key={agent.id}
                  className="group rounded-2xl border border-[#2B2B2B] bg-[#191919] hover:border-primary transition-all p-5 min-h-[200px] flex flex-col"
                >
                  <div className="flex items-start justify-between">
                    <button
                      onClick={() => onNavigateToMarketplace(agent.id)}
                      className={`market-icon market-icon--${agent.tone} !w-14 !h-14 !rounded-2xl flex items-center justify-center group-hover:scale-105 transition`}
                    >
                      <span className="material-symbols-outlined text-[28px] text-white">
                        {agent.icon}
                      </span>
                    </button>

                    <button
                      onClick={() => onUninstallClick(agent)}
                      className="w-9 h-9 rounded-lg hover:bg-red-500/10 text-[#8A8A8A] hover:text-red-500 transition"
                    >
                      <span className="material-symbols-outlined">delete</span>
                    </button>
                  </div>

                  <div className="mt-5 flex-1">
                    <h4 className="text-white text-base font-semibold">
                      {agent.name}
                    </h4>

                    <p className="mt-2 text-sm text-[#9B9B9B] leading-relaxed line-clamp-4">
                      {agent.description}
                    </p>
                  </div>

                  <button
                    onClick={() => onNavigateToMarketplace(agent.id)}
                    className="mt-6 text-primary text-sm font-medium hover:underline self-start"
                  >
                    View Details →
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Footer */}

      <div className="border-t border-[#262626] px-8 py-5 flex items-center justify-end">
        <button
          onClick={() => onNavigateToMarketplace(null)}
          className="px-6 py-2 rounded-lg bg-primary text-on-primary font-medium hover:opacity-90 transition"
        >
          Browse Marketplace
        </button>
      </div>
    </div>
  );
}
