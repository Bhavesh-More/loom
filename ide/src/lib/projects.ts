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