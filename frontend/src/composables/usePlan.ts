import { ref, onUnmounted } from 'vue'
import type { PlanEntry } from '../types'
import { api } from '../services/api'
import { withLoading } from '../utils/withLoading'
import { useLogs } from './useLogs'

const PLAN_POLL_INTERVAL_MS = 5_000

const plan = ref<PlanEntry[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

export function usePlan() {
  const load = <T>(fn: () => Promise<T>) => withLoading(isLoading, error, fn)
  const { fetchLogs } = useLogs()

  const fetchPlan = () =>
    load(async () => {
      ;[plan.value] = await Promise.all([api.fetchPlan(), fetchLogs()])
    })

  const startPolling = () => {
    const id = setInterval(fetchPlan, PLAN_POLL_INTERVAL_MS)
    onUnmounted(() => clearInterval(id))
    return fetchPlan()
  }

  return { plan, isLoading, error, fetchPlan, startPolling }
}
