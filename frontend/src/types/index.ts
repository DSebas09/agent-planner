export type Priority = 'high' | 'medium' | 'low'
export type EnergyLevel = 'high' | 'medium' | 'low'
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'postponed'
export type AgentTrigger =
  | 'task_added'
  | 'task_started'
  | 'task_completed'
  | 'task_updated'
  | 'task_deleted'
  | 'delay_reported'

export interface TaskCreate {
  title: string
  priority: Priority
  energy_required: EnergyLevel
  estimated_minutes: number
  deadline: string | null
}

export interface Task {
  id: number
  title: string
  priority: Priority
  energy_required: EnergyLevel
  estimated_minutes: number
  actual_minutes: number | null
  deadline: string | null
  status: TaskStatus
  created_at: string
}

export interface PlanEntry {
  position: number
  scheduled_start: string
  scheduled_end: string
  task: Task
}

export interface TaskUpdate {
  title?: string
  priority?: Priority
  energy_required?: EnergyLevel
  estimated_minutes?: number
  deadline?: string | null
}

export interface AgentLog {
  id: number
  timestamp: string
  trigger: AgentTrigger
  message: string
}
