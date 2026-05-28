import { ref } from 'vue'
import type { Task, TaskCreate, TaskUpdate } from '../types'
import { api } from '../services/api'
import { withLoading } from '../utils/withLoading'

const tasks = ref<Task[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

export function useTasks() {
    const load = <T>(fn: () => Promise<T>) => withLoading(isLoading, error, fn)

    const fetchTasks = () =>
    load(async () => {
        tasks.value = await api.fetchTasks()
    })

    const createTask = (payload: TaskCreate) =>
    load(async () => {
        const task = await api.createTask(payload)
        tasks.value = [...tasks.value, task]
    })

    const updateTask = (id: number, payload: TaskUpdate) =>
    load(async () => {
        await api.updateTask(id, payload)
        tasks.value = await api.fetchTasks()
    })

    const deleteTask = (id: number) =>
    load(async () => {
        await api.deleteTask(id)
        tasks.value = tasks.value.filter(t => t.id !== id)
    })

    const startTask = (id: number) =>
    load(async () => {
        await api.startTask(id)
        tasks.value = await api.fetchTasks()
    })

    const completeTask = (id: number, actualMinutes: number) =>
    load(async () => {
        await api.completeTask(id, actualMinutes)
        tasks.value = await api.fetchTasks()
    })

    const reportDelay = (id: number, extraMinutes: number) =>
    load(async () => {
        await api.reportDelay(id, extraMinutes)
        tasks.value = await api.fetchTasks()
    })

    return {
        tasks,
        isLoading,
        error,
        fetchTasks,
        createTask,
        updateTask,
        deleteTask,
        startTask,
        completeTask,
        reportDelay,
    }
}
