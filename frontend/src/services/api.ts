import type { AgentLog, PlanEntry, Task, TaskCreate, TaskUpdate } from '../types'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return (await res.json()) as T
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined })

const patch = <T>(path: string, body: unknown) =>
  request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })

export const api = {
  fetchTasks:   () => request<Task[]>('/tasks'),
  fetchTask:    (id: number) => request<Task>(`/tasks/${id}`),
  createTask:   (payload: TaskCreate) => post<Task>('/tasks', payload),
  updateTask:   (id: number, payload: TaskUpdate) => patch<PlanEntry[]>(`/tasks/${id}`, payload),
  deleteTask:   (id: number) => request<PlanEntry[]>(`/tasks/${id}`, { method: 'DELETE' }),
  startTask:    (id: number) => post<PlanEntry[]>(`/tasks/${id}/start`),
  completeTask: (id: number, actualMinutes: number) => post<PlanEntry[]>(`/tasks/${id}/complete`, { actual_minutes: actualMinutes }),
  reportDelay:  (id: number, extraMinutes: number) => post<PlanEntry[]>(`/tasks/${id}/delay`, { extra_minutes: extraMinutes }),
  fetchPlan:    () => request<PlanEntry[]>('/plan'),
  fetchLogs:    () => request<AgentLog[]>('/logs'),
}
