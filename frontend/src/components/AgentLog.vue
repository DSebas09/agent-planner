<script setup lang="ts">
import type { AgentLog } from '../types'

interface Props {
  logs: AgentLog[]
}

defineProps<Props>()

const triggerColor: Record<string, string> = {
  task_added:     'bg-blue-100 text-blue-700',
  task_started:   'bg-green-100 text-green-700',
  task_completed: 'bg-purple-100 text-purple-700',
  task_updated:   'bg-yellow-100 text-yellow-700',
  task_deleted:   'bg-red-100 text-red-700',
  delay_reported: 'bg-orange-100 text-orange-700',
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="flex flex-col gap-2 overflow-y-auto">
    <p v-if="logs.length === 0" class="text-sm text-gray-400 text-center py-4">
      No agent activity yet.
    </p>

    <div
      v-for="log in [...logs].reverse()"
      :key="log.id"
      class="flex flex-col gap-1 border-l-2 border-gray-200 pl-3 py-1"
    >
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-400">{{ formatTime(log.timestamp) }}</span>
        <span :class="triggerColor[log.trigger]" class="text-xs font-medium px-2 py-0.5 rounded-full">
          {{ log.trigger }}
        </span>
      </div>
      <p class="text-sm text-gray-700">{{ log.message }}</p>
    </div>
  </div>
</template>

<style scoped></style>
