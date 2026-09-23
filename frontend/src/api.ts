export type Language = { code: string; label: string }

export type Config = {
  user: string
  has_password: boolean
  has_deepgram: boolean
  has_session: boolean
  languages: Language[]
  default_language: string
}

export type Course = {
  id: string
  title: string
  professor: string
  podcasts: number
  url: string
}

export type Podcast = { id: string; title: string; date: string }

export type PodcastList = {
  student_id: string
  podcasts: Podcast[]
  default_output_dir: string
}

export type ItemStatus = 'pending' | 'downloading' | 'transcribing' | 'done' | 'error' | 'cancelled'

export type JobItem = {
  podcast: Podcast
  status: ItemStatus
  log: string[]
  mp3: string | null
  txt: string | null
}

export type Job = {
  id: string
  status: 'running' | 'finished'
  output_dir: string
  items: JobItem[]
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : `Erreur ${res.status}`
    throw new Error(detail)
  }
  return data as T
}

export const api = {
  getConfig: () => request<Config>('GET', '/api/config'),
  saveConfig: (body: { user: string; password: string; deepgram_key: string }) =>
    request<Config>('PUT', '/api/config', body),
  login: () => request<Config>('POST', '/api/login'),
  listCourses: () => request<Course[]>('GET', '/api/courses'),
  listPodcasts: (url: string) => request<PodcastList>('POST', '/api/podcasts', { url }),
  createJob: (body: {
    podcasts: Podcast[]
    student_id: string
    output_dir: string
    language: string
    transcribe: boolean
  }) => request<Job>('POST', '/api/jobs', body),
  getJob: (id: string) => request<Job>('GET', `/api/jobs/${id}`),
  cancelJob: (id: string) => request<Job>('POST', `/api/jobs/${id}/cancel`),
  readTranscript: (path: string) => request<{ text: string }>('POST', '/api/transcript', { path }),
  open: (path: string) => request<{ ok: boolean }>('POST', '/api/open', { path }),
}
