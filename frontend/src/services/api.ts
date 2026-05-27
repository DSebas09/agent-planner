import type { AgentLog, PlanEntry, Task, TaskCreate, TaskUpdate } from '../types'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const api = {
  fetchTasks:   () => request<Task[]>('/tasks'),
  fetchTask:    (id: number) => request<Task>(`/tasks/${id}`),
  createTask:   (payload: TaskCreate) => request<Task>('/tasks', { method: 'POST', body: JSON.stringify(payload) }),
  updateTask:   (id: number, payload: TaskUpdate) => request<PlanEntry[]>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteTask:   (id: number) => request<PlanEntry[]>(`/tasks/${id}`, { method: 'DELETE' }),
  startTask:    (id: number) => request<PlanEntry[]>(`/tasks/${id}/start`, { method: 'POST' }),
  completeTask: (id: number, actualMinutes: number) => request<PlanEntry[]>(`/tasks/${id}/complete`, { method: 'POST', body: JSON.stringify({ actual_minutes: actualMinutes }) }),
  reportDelay:  (id: number, extraMinutes: number) => request<PlanEntry[]>(`/tasks/${id}/delay`, { method: 'POST', body: JSON.stringify({ extra_minutes: extraMinutes }) }),
  fetchPlan:    () => request<PlanEntry[]>('/plan'),
  fetchLogs:    () => request<AgentLog[]>('/logs'),
}
