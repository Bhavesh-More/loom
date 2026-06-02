import { useState } from 'react'
import { type FileTreeNode } from '../lib/projects'

type FileExplorerProps = {
  tree: FileTreeNode[]
  activeFilePath: string | null
  onSelectFile: (path: string) => void
}

export default function FileExplorer({ tree, activeFilePath, onSelectFile }: FileExplorerProps) {
  return (
    <div className="flex flex-col h-full overflow-y-auto font-body-sm text-[13px] text-on-surface">
      {tree.length === 0 ? (
        <div className="p-4 text-on-surface-variant italic">No files in workspace</div>
      ) : (
        <div className="py-2 flex flex-col">
          {tree.map((node) => (
            <TreeNode
              key={node.path}
              node={node}
              activeFilePath={activeFilePath}
              onSelectFile={onSelectFile}
              depth={0}
            />
          ))}
        </div>
      )}
    </div>
  )
}

type TreeNodeProps = {
  node: FileTreeNode
  activeFilePath: string | null
  onSelectFile: (path: string) => void
  depth: number
}

function TreeNode({ node, activeFilePath, onSelectFile, depth }: TreeNodeProps) {
  const isDirectory = node.type === 'directory'
  const [isOpen, setIsOpen] = useState(true) // Default to open for easy visibility

  const isActive = activeFilePath === node.path

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (isDirectory) {
      setIsOpen(!isOpen)
    } else {
      onSelectFile(node.path)
    }
  }

  const getFileIcon = (filename: string): string => {
    if (filename.endsWith('.py')) return 'code'
    if (filename.endsWith('.sql')) return 'database'
    if (filename.endsWith('.yml') || filename.endsWith('.yaml')) return 'settings'
    if (filename.endsWith('.md')) return 'description'
    if (filename.endsWith('.txt')) return 'description'
    if (filename.endsWith('.js') || filename.endsWith('.ts') || filename.endsWith('.tsx') || filename.endsWith('.jsx')) return 'code'
    return 'description'
  }

  const getFileColorClass = (filename: string): string => {
    if (filename.endsWith('.py')) return 'text-primary'
    if (filename.endsWith('.sql')) return 'text-secondary'
    if (filename.endsWith('.yml') || filename.endsWith('.yaml')) return 'text-on-surface-variant'
    if (filename.endsWith('.md')) return 'text-secondary'
    if (filename.endsWith('.js') || filename.endsWith('.ts') || filename.endsWith('.tsx') || filename.endsWith('.jsx')) return 'text-[#61DAFB]'
    return 'text-on-surface-variant'
  }

  return (
    <div className="flex flex-col select-none">
      {/* Node Row */}
      <div
        onClick={handleToggle}
        style={{ paddingLeft: `${depth * 16 + 12}px` }}
        className={`flex items-center gap-2 py-1.5 pr-3 cursor-pointer transition-all duration-150 rounded border-l-2 ${
          isActive
            ? 'bg-[#1e1e1e] text-primary border-primary font-medium'
            : 'hover:bg-[#121212] border-transparent text-on-surface-variant hover:text-on-surface'
        }`}
      >
        {isDirectory ? (
          <>
            <span 
              className="material-symbols-outlined text-[16px] text-on-surface-variant transition-transform duration-200 shrink-0" 
              style={{ transform: isOpen ? 'rotate(90deg)' : 'none' }}
            >
              chevron_right
            </span>
            <span className="material-symbols-outlined text-[18px] text-[#cca025] shrink-0">
              {isOpen ? 'folder_open' : 'folder'}
            </span>
          </>
        ) : (
          <>
            <span className="w-4 shrink-0" />
            <span className={`material-symbols-outlined text-[18px] shrink-0 ${getFileColorClass(node.name)}`}>
              {getFileIcon(node.name)}
            </span>
          </>
        )}
        <span className="truncate">{node.name}</span>
      </div>

      {/* Children list */}
      {isDirectory && isOpen && node.children && (
        <div className="flex flex-col">
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              activeFilePath={activeFilePath}
              onSelectFile={onSelectFile}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
