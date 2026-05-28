import { ref } from 'vue'
import type { AgentLog } from '../types'
import { api } from '../services/api'
import { withLoading } from '../utils/withLoading'

const logs = ref<AgentLog[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

export function useLogs() {
  const fetchLogs = () =>
    withLoading(isLoading, error, async () => {
      logs.value = await api.fetchLogs()
    })

  return { logs, isLoading, error, fetchLogs }
}
