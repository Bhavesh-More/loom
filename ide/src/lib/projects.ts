const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type Project = {
  id: string
  name: string
}

let cachedProjects: Project[] | null = null
let projectsFetchPromise: Promise<Project[]> | null = null

export function invalidateProjectsCache() {
  cachedProjects = null
  projectsFetchPromise = null
}

export async function getProjects(forceRefresh = false): Promise<Project[]> {
  if (forceRefresh) {
    invalidateProjectsCache()
  }

  if (cachedProjects) {
    return cachedProjects
  }

  if (projectsFetchPromise) {
    return projectsFetchPromise
  }

  projectsFetchPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL.replace(/\/$/, '')}/projects/get-projects`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error('Failed to fetch projects')
      }

      const data = await response.json()
      cachedProjects = data
      return data
    } finally {
      projectsFetchPromise = null
    }
  })()

  return projectsFetchPromise
}

export async function developProject(projectId: string, prompt: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL.replace(/\/$/, '')}/projects/develop`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      project_id: projectId,
      prompt: prompt,
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    let errorMsg = 'Failed to develop project'
    try {
      const parsed = JSON.parse(errorText)
      errorMsg = parsed.detail || errorMsg
    } catch {
      errorMsg = errorText || errorMsg
    }
    throw new Error(errorMsg)
  }

  return response.json()
}

export async function developProjectStream(
  projectId: string,
  prompt: string,
  onChunk: (chunk: any) => void
): Promise<void> {
  const response = await fetch(`${API_BASE_URL.replace(/\/$/, '')}/projects/develop`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      project_id: projectId,
      prompt: prompt,
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    let errorMsg = 'Failed to develop project'
    try {
      const parsed = JSON.parse(errorText)
      errorMsg = parsed.detail || errorMsg
    } catch {
      errorMsg = errorText || errorMsg
    }
    throw new Error(errorMsg)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  if (reader) {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.trim()) {
          try {
            const chunk = JSON.parse(line)
            onChunk(chunk)
          } catch (e) {
            console.error('Failed to parse chunk', e)
          }
        }
      }
    }
  }
}