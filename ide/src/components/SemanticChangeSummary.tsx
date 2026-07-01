import type { FC } from 'react'

/**
 * SemanticChangeSummary — displays a structured, human-readable summary of
 * all changes made during a pipeline run, annotated with risk badges.
 *
 * Data comes from either:
 *   a) The _patch.semantic_summary arrays in agent output (live during run)
 *   b) GET /api/audit/{run_id}/summary (post-run from audit ledger)
 */

export type AgentChange = {
  agentId: string
  semanticSummary: string[]
  riskLevel: 'low' | 'medium' | 'high'
  filesChanged: number
  linesChanged: number
  withinBudget: boolean
  requiresApproval: boolean
  buildStatus?: string
  confidenceScore?: number
}

const RISK_CONFIG = {
  low:    { label: 'Low Risk',    color: 'text-[#4ade80]',  bg: 'bg-[#4ade80]/10',  border: 'border-[#4ade80]/20',  icon: 'shield' },
  medium: { label: 'Med Risk',    color: 'text-[#facc15]',  bg: 'bg-[#facc15]/10',  border: 'border-[#facc15]/20',  icon: 'warning' },
  high:   { label: 'High Risk',   color: 'text-[#ef4444]',  bg: 'bg-[#ef4444]/10',  border: 'border-[#ef4444]/20',  icon: 'error' },
}

const BUILD_CONFIG: Record<string, { icon: string; color: string }> = {
  passed:  { icon: 'check_circle', color: 'text-[#4ade80]'         },
  failed:  { icon: 'cancel',       color: 'text-[#ef4444]'         },
  unknown: { icon: 'help',         color: 'text-on-surface-variant' },
  skipped: { icon: 'skip_next',    color: 'text-on-surface-variant' },
}

type AgentChangeCardProps = { change: AgentChange }

function AgentChangeCard({ change }: AgentChangeCardProps) {
  const risk = RISK_CONFIG[change.riskLevel] ?? RISK_CONFIG.low
  const build = BUILD_CONFIG[change.buildStatus ?? 'unknown'] ?? BUILD_CONFIG.unknown

  return (
    <div className={`glass-panel rounded-xl border ${risk.border} p-4 flex flex-col gap-3 animate-step-fade-in`}>
      {/* Header row */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] text-primary">smart_toy</span>
          <span className="font-medium text-[13px] text-white">
            {change.agentId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} Agent
          </span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Risk badge */}
          <span className={`flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full ${risk.bg} ${risk.color} border ${risk.border}`}>
            <span className="material-symbols-outlined text-[12px]">{risk.icon}</span>
            {risk.label}
          </span>

          {/* Budget violation badge */}
          {!change.withinBudget && (
            <span className="flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-[#fb923c]/10 text-[#fb923c] border border-[#fb923c]/20">
              <span className="material-symbols-outlined text-[12px]">rule</span>
              Over Budget
            </span>
          )}

          {/* Approval needed badge */}
          {change.requiresApproval && (
            <span className="flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-[#a78bfa]/10 text-[#a78bfa] border border-[#a78bfa]/20">
              <span className="material-symbols-outlined text-[12px]">approval</span>
              Needs Approval
            </span>
          )}

          {/* Build status */}
          <span className={`material-symbols-outlined text-[16px] ${build.color}`} title={`Build: ${change.buildStatus}`}>
            {build.icon}
          </span>
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 text-[12px] text-on-surface-variant font-code-md">
        <span className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[14px]">description</span>
          {change.filesChanged} file{change.filesChanged !== 1 ? 's' : ''}
        </span>
        <span className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[14px]">data_array</span>
          {change.linesChanged} lines
        </span>
        {change.confidenceScore !== undefined && (
          <span className="flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">bar_chart</span>
            {Math.round(change.confidenceScore * 100)}% confidence
          </span>
        )}
      </div>

      {/* Semantic change list */}
      {change.semanticSummary.length > 0 && (
        <ul className="flex flex-col gap-1">
          {change.semanticSummary.map((item, idx) => (
            <li key={idx} className="text-[13px] text-on-surface leading-relaxed flex items-start gap-2">
              <span className="shrink-0 text-[#4ade80] text-[14px]">✓</span>
              <span>{item.replace(/^✅\s*/, '')}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

type SemanticChangeSummaryProps = {
  changes: AgentChange[]
  runId?: string
  isVisible: boolean
}

const SemanticChangeSummary: FC<SemanticChangeSummaryProps> = ({ changes, runId, isVisible }) => {
  if (!isVisible || changes.length === 0) return null

  const highCount   = changes.filter((c: AgentChange) => c.riskLevel === 'high').length
  const medCount    = changes.filter((c: AgentChange) => c.riskLevel === 'medium').length
  const lowCount    = changes.filter((c: AgentChange) => c.riskLevel === 'low').length
  const totalFiles  = changes.reduce((s: number, c: AgentChange) => s + c.filesChanged, 0)
  const totalLines  = changes.reduce((s: number, c: AgentChange) => s + c.linesChanged, 0)
  const approvalNeeded = changes.filter((c: AgentChange) => c.requiresApproval).length

  return (
    <div className="flex flex-col gap-4 animate-step-fade-in">
      {/* Summary header */}
      <div className="glass-panel rounded-xl border border-outline-variant/20 p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="material-symbols-outlined text-[18px] text-primary">summarize</span>
          <span className="font-medium text-[14px] text-white">Semantic Change Summary</span>
          {runId && (
            <span className="text-[11px] text-on-surface-variant font-code-md ml-auto">run: {runId}</span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="flex flex-col gap-0.5">
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Files</span>
            <span className="text-[20px] font-bold text-white">{totalFiles}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Lines</span>
            <span className="text-[20px] font-bold text-white">{totalLines}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Risk</span>
            <div className="flex items-center gap-1.5 mt-1">
              {highCount > 0 && <span className="text-[11px] text-[#ef4444] font-medium">{highCount}H</span>}
              {medCount  > 0 && <span className="text-[11px] text-[#facc15] font-medium">{medCount}M</span>}
              {lowCount  > 0 && <span className="text-[11px] text-[#4ade80] font-medium">{lowCount}L</span>}
            </div>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Approval</span>
            <span className={`text-[20px] font-bold ${approvalNeeded > 0 ? 'text-[#a78bfa]' : 'text-[#4ade80]'}`}>
              {approvalNeeded > 0 ? `${approvalNeeded} needed` : 'None'}
            </span>
          </div>
        </div>
      </div>

      {/* Per-agent cards */}
      <div className="flex flex-col gap-3">
        {changes.map((change: AgentChange) => (
          <AgentChangeCard key={change.agentId} change={change} />
        ))}
      </div>
    </div>
  )
}

export default SemanticChangeSummary
