import { useEffect, useState, useRef } from 'react'
import Editor from '@monaco-editor/react'

type CodeEditorProps = {
  filePath: string
  content: string
  onSave: (path: string, newContent: string) => Promise<void> | void
  isSaving?: boolean
}

export default function CodeEditor({ filePath, content, onSave, isSaving = false }: CodeEditorProps) {
  const [editorValue, setEditorValue] = useState(content)
  const isDirty = editorValue !== content
  const editorRef = useRef<any>(null)

  // Update internal value when the file or external content changes
  useEffect(() => {
    setEditorValue(content)
  }, [content, filePath])

  // Get Monaco editor language from path
  const getLanguageFromPath = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'py': return 'python'
      case 'js': return 'javascript'
      case 'jsx': return 'javascript'
      case 'ts': return 'typescript'
      case 'tsx': return 'typescript'
      case 'json': return 'json'
      case 'html': return 'html'
      case 'css': return 'css'
      case 'md': return 'markdown'
      case 'sql': return 'sql'
      case 'sh': return 'shell'
      case 'yml': return 'yaml'
      case 'yaml': return 'yaml'
      default: return 'plaintext'
    }
  }

  const handleSave = () => {
    if (isDirty && !isSaving) {
      onSave(filePath, editorValue)
    }
  }

  // Handle Ctrl+S key combination inside Monaco Editor
  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor
    
    // Add command for Save (Ctrl+S or Cmd+S)
    editor.addCommand(
      2048 | 49, // KeyMod.CtrlCmd | KeyCode.KeyS
      () => {
        // Trigger save if dirty
        if (editorRef.current) {
          const val = editorRef.current.getValue()
          if (val !== content) {
            onSave(filePath, val)
          }
        }
      }
    )
  }

  const filename = filePath.split('/').pop() || filePath

  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] border border-[#262626] rounded-lg overflow-hidden animate-step-fade-in">
      {/* Editor Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#171717] border-b border-[#262626] select-none shrink-0">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] text-on-surface-variant">description</span>
          <span className="text-[13px] font-code-md text-primary font-medium">{filename}</span>
          <span className="text-[11px] font-code-md text-on-surface-variant font-light truncate max-w-xs">{filePath}</span>
          {isDirty && (
            <span className="w-2 h-2 rounded-full bg-primary" title="Unsaved changes" />
          )}
        </div>

        <div className="flex items-center gap-2">
          {isSaving && (
            <span className="text-[12px] text-on-surface-variant flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px] animate-spin">sync</span>
              Saving...
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={!isDirty || isSaving}
            className={`flex items-center gap-1 px-2.5 py-1 rounded text-[12px] font-medium transition-all ${
              isDirty && !isSaving
                ? 'bg-primary text-on-primary hover:bg-opacity-90 active:scale-95 cursor-pointer'
                : 'bg-[#2b2b2b] text-on-surface-variant opacity-60 cursor-not-allowed'
            }`}
            type="button"
          >
            <span className="material-symbols-outlined text-[14px]">save</span>
            <span>Save</span>
          </button>
        </div>
      </div>

      {/* Monaco Editor Component */}
      <div className="flex-1 min-h-0 relative">
        <Editor
          height="100%"
          language={getLanguageFromPath(filePath)}
          theme="vs-dark"
          value={editorValue}
          onChange={(val) => setEditorValue(val || '')}
          onMount={handleEditorDidMount}
          loading={
            <div className="absolute inset-0 flex items-center justify-center bg-[#1e1e1e] text-on-surface-variant gap-2">
              <span className="material-symbols-outlined animate-spin">sync</span>
              <span>Loading Editor...</span>
            </div>
          }
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: 'Fira Code, Menlo, Monaco, Consolas, Courier New, monospace',
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            readOnly: isSaving,
            theme: 'vs-dark',
            automaticLayout: true,
            tabSize: 4,
            padding: { top: 8, bottom: 8 }
          }}
        />
      </div>
    </div>
  )
}
