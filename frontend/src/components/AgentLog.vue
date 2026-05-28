<script setup lang="ts">
import type { AgentLog } from '../types'

interface Props {
  logs: AgentLog[]
}

defineProps<Props>()

const triggerColor: Record<string, string> = {
  task_added:     'text-emerald-400',
  task_started:   'text-blue-400',
  task_completed: 'text-violet-400',
  task_updated:   'text-amber-400',
  task_deleted:   'text-red-400',
  delay_reported: 'text-orange-400',
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="bg-gray-950 rounded-xl px-4 py-3 font-mono text-xs overflow-y-auto h-44 flex flex-col-reverse">
    <div v-if="logs.length === 0" class="text-gray-600">
      $ waiting for agent activity...
    </div>

    <div
      v-for="log in logs"
      :key="log.id"
      class="flex gap-3 py-0.5 leading-relaxed"
    >
      <span class="text-gray-600 shrink-0">{{ formatTime(log.timestamp) }}</span>
      <span :class="triggerColor[log.trigger]" class="shrink-0 w-36">{{ log.trigger }}</span>
      <span class="text-gray-300">{{ log.message }}</span>
    </div>
  </div>
</template>

<style scoped></style>
