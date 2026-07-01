import type { FC } from 'react'

/**
 * AgentTreePanel — real-time agent execution tree visualization.
 *
 * Renders the hierarchical TaskGraph produced by the MasterPlanner as a
 * live tree where each node reflects its current execution status.
 *
 * Props:
 *   nodes       – Array of TaskGraph nodes from the SSE planner event.
 *   logs        – Array of task_graph_logs strings (e.g. "[db_node] agent=postgresql status=success").
 *   isRunning   – Whether the pipeline is still executing.
 */

export type TaskNode = {
  id: string
  parentId?: string | null
  agentId: string
  task: string
  dependsOn?: string[]
  capabilityScore?: number
  selectionReasoning?: string
}

type NodeStatus = 'pending' | 'running' | 'completed' | 'failed'

function inferStatus(nodeId: string, logs: string[]): NodeStatus {
  const logLine = logs.find((l) => l.includes(`[${nodeId}]`))
  if (!logLine) return 'pending'
  if (logLine.includes('status=success') || logLine.includes('completed')) return 'completed'
  if (logLine.includes('status=failed') || logLine.includes('failed')) return 'failed'
  if (logLine.includes('running')) return 'running'
  return 'completed' // if a log exists without explicit status, assume completed
}

const STATUS_CONFIG: Record<NodeStatus, { icon: string; color: string; label: string; pulse: boolean }> = {
  pending:   { icon: 'schedule',          color: 'text-on-surface-variant',    label: 'Pending',   pulse: false },
  running:   { icon: 'progress_activity', color: 'text-secondary',             label: 'Running',   pulse: true  },
  completed: { icon: 'check_circle',      color: 'text-[#4ade80]',             label: 'Done',      pulse: false },
  failed:    { icon: 'error',             color: 'text-[#ef4444]',             label: 'Failed',    pulse: false },
}

const AGENT_COLORS: Record<string, string> = {
  postgresql:     '#60a5fa',
  mongodb:        '#34d399',
  fastapi:        '#a78bfa',
  auth:           '#fb923c',
  streamlit:      '#f472b6',
  redis:          '#f87171',
  docker:         '#38bdf8',
  github_actions: '#facc15',
  pytest:         '#c084fc',
  rag:            '#2dd4bf',
  all_rounder:    '#94a3b8',
}

function agentColor(agentId: string): string {
  return AGENT_COLORS[agentId] ?? '#94a3b8'
}

type TreeNodeProps = {
  node: TaskNode
  depth: number
  status: NodeStatus
  children: TaskNode[]
  logs: string[]
}

function TreeNodeRow({ node, depth, status, children, logs }: TreeNodeProps) {
  const cfg = STATUS_CONFIG[status]
  const color = agentColor(node.agentId)
  const indent = depth * 20

  return (
    <div>
      <div
        className="flex items-start gap-2.5 py-1.5 px-2 rounded-lg hover:bg-white/5 transition-colors group"
        style={{ paddingLeft: `${8 + indent}px` }}
      >
        {/* Connector line for non-root nodes */}
        {depth > 0 && (
          <div className="w-4 shrink-0 flex flex-col items-center" aria-hidden>
            <div className="w-px flex-1 bg-white/10" />
            <div className="w-2 h-px bg-white/10" />
          </div>
        )}

        {/* Agent color badge */}
        <div
          className="w-2 h-2 rounded-full shrink-0 mt-1.5"
          style={{ backgroundColor: color }}
          title={node.agentId}
        />

        {/* Status icon */}
        <span
          className={`material-symbols-outlined text-[15px] shrink-0 mt-0.5 ${cfg.color} ${cfg.pulse ? 'animate-spin' : ''}`}
          aria-label={cfg.label}
        >
          {cfg.icon}
        </span>

        {/* Node info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-[13px] text-white">
              {node.agentId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
            <span className="text-[11px] text-on-surface-variant font-code-md">
              #{node.id}
            </span>
            {status === 'running' && (
              <span className="text-[11px] bg-secondary/20 text-secondary px-1.5 py-0.5 rounded-full animate-pulse">
                active
              </span>
            )}
            {status === 'failed' && (
              <span className="text-[11px] bg-[#ef4444]/20 text-[#ef4444] px-1.5 py-0.5 rounded-full">
                failed
              </span>
            )}
          </div>
          <p className="text-[12px] text-on-surface-variant mt-0.5 leading-relaxed truncate group-hover:whitespace-normal">
            {node.task}
          </p>
          {node.dependsOn && node.dependsOn.length > 0 && (
            <p className="text-[11px] text-on-surface-variant/50 mt-0.5">
              depends on: {node.dependsOn.join(', ')}
            </p>
          )}
        </div>

        {/* Confidence badge */}
        {node.capabilityScore !== undefined && (
          <span className="text-[11px] font-code-md text-on-surface-variant shrink-0">
            {Math.round(node.capabilityScore * 100)}%
          </span>
        )}
      </div>

      {/* Children */}
      {children.map((child) => (
        <TreeNodeRow
          key={child.id}
          node={child}
          depth={depth + 1}
          status={inferStatus(child.id, logs)}
          children={[]} // TODO: support deeper nesting if needed
          logs={logs}
        />
      ))}
    </div>
  )
}

type AgentTreePanelProps = {
  nodes: TaskNode[]
  logs: string[]
  isRunning: boolean
}

const AgentTreePanel: FC<AgentTreePanelProps> = ({ nodes, logs, isRunning }) => {
  if (!nodes || nodes.length === 0) return null

  // Build parent→children map
  const childrenMap: Record<string, TaskNode[]> = {}
  const rootNodes: TaskNode[] = []

  nodes.forEach((node) => {
    if (!node.parentId) {
      rootNodes.push(node)
    } else {
      if (!childrenMap[node.parentId]) childrenMap[node.parentId] = []
      childrenMap[node.parentId].push(node)
    }
  })

  const completedCount = nodes.filter((n) => inferStatus(n.id, logs) === 'completed').length
  const failedCount    = nodes.filter((n) => inferStatus(n.id, logs) === 'failed').length
  const progress       = nodes.length > 0 ? (completedCount / nodes.length) * 100 : 0

  return (
    <div className="glass-panel rounded-xl border border-outline-variant/20 overflow-hidden animate-step-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-primary">account_tree</span>
          <span className="text-[13px] font-medium text-white">Agent Execution Tree</span>
          {isRunning && (
            <span className="w-1.5 h-1.5 bg-secondary rounded-full animate-pulse" />
          )}
        </div>
        <div className="flex items-center gap-3 text-[12px] text-on-surface-variant">
          <span className="text-[#4ade80]">✓ {completedCount}</span>
          {failedCount > 0 && <span className="text-[#ef4444]">✗ {failedCount}</span>}
          <span>{nodes.length} total</span>
        </div>
      </div>

      {/* Progress bar */}
      {nodes.length > 0 && (
        <div className="h-0.5 bg-white/5">
          <div
            className="h-full bg-primary transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Tree */}
      <div className="p-2 max-h-72 overflow-y-auto hide-scrollbar flex flex-col">
        {rootNodes.length > 0
          ? rootNodes.map((node) => (
              <TreeNodeRow
                key={node.id}
                node={node}
                depth={0}
                status={inferStatus(node.id, logs)}
                children={childrenMap[node.id] ?? []}
                logs={logs}
              />
            ))
          : nodes.map((node) => (
              <TreeNodeRow
                key={node.id}
                node={node}
                depth={0}
                status={inferStatus(node.id, logs)}
                children={childrenMap[node.id] ?? []}
                logs={logs}
              />
            ))}
      </div>
    </div>
  )
}

export default AgentTreePanel
