<script setup lang="ts">
import { ref, computed } from 'vue'
import type { PlanEntry } from '../types'

interface Props {
  entry: PlanEntry
  error?: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  start:    [id: number]
  complete: [id: number, actualMinutes: number]
  delay:    [id: number, extraMinutes: number]
  delete:   [id: number]
}>()

const showCompleteForm = ref(false)
const showDelayForm = ref(false)
const actualMinutes = ref(props.entry.task.estimated_minutes)
const extraMinutes = ref(15)

const deadlineLabel = computed(() => {
  if (!props.entry.task.deadline) return null
  const diff = new Date(props.entry.task.deadline).getTime() - Date.now()
  if (diff < 0) return 'Overdue'
  const hours = diff / 1000 / 60 / 60
  return hours >= 24 ? `${Math.floor(hours / 24)}d left` : `${Math.floor(hours)}h left`
})

const deadlineClass = computed(() => {
  if (!props.entry.task.deadline) return ''
  const diff = new Date(props.entry.task.deadline).getTime() - Date.now()
  if (diff < 0) return 'bg-red-500 text-white'
  return diff / 1000 / 60 / 60 < 24 ? 'bg-orange-400 text-white' : 'bg-gray-200 text-gray-600'
})

const priorityBorder: Record<string, string> = {
  high:   'border-l-red-500',
  medium: 'border-l-amber-400',
  low:    'border-l-emerald-500',
}

const priorityBadge: Record<string, string> = {
  high:   'bg-red-500 text-white',
  medium: 'bg-amber-400 text-white',
  low:    'bg-emerald-500 text-white',
}

const statusBg: Record<string, string> = {
  pending:     'bg-white',
  in_progress: 'bg-blue-50',
  completed:   'bg-emerald-50',
  postponed:   'bg-amber-50',
}

const statusBadge: Record<string, string> = {
  pending:     'bg-gray-200 text-gray-700',
  in_progress: 'bg-blue-500 text-white',
  completed:   'bg-emerald-500 text-white',
  postponed:   'bg-amber-400 text-white',
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function handleComplete() {
  emit('complete', props.entry.task.id, actualMinutes.value)
  showCompleteForm.value = false
}

function handleDelay() {
  emit('delay', props.entry.task.id, extraMinutes.value)
  showDelayForm.value = false
}
</script>

<template>
  <div
    :class="[statusBg[entry.task.status], priorityBorder[entry.task.priority]]"
    class="border-l-4 rounded-lg border border-gray-100 shadow-sm"
  >
    <div class="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3">
      <span class="w-full md:w-auto shrink-0 font-mono text-xs text-gray-400">
        <span class="font-bold text-gray-500">#{{ entry.position }}</span>
        · {{ formatTime(entry.scheduled_start) }}–{{ formatTime(entry.scheduled_end) }}
      </span>
      <p class="flex-1 font-semibold text-gray-900 min-w-0 truncate">{{ entry.task.title }}</p>
      <span v-if="deadlineLabel" :class="deadlineClass" class="shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full">
        {{ deadlineLabel }}
      </span>
    </div>

    <div class="flex flex-wrap items-center gap-2 px-4 pb-3">
      <div class="flex gap-1.5 flex-1 flex-wrap">
        <span :class="priorityBadge[entry.task.priority]" class="text-xs font-semibold px-2.5 py-0.5 rounded-full">
          {{ entry.task.priority }}
        </span>
        <span class="bg-violet-500 text-white text-xs font-semibold px-2.5 py-0.5 rounded-full">
          {{ entry.task.energy_required }} energy
        </span>
        <span :class="statusBadge[entry.task.status]" class="text-xs font-semibold px-2.5 py-0.5 rounded-full">
          {{ entry.task.status.replace('_', ' ') }}
        </span>
        <span class="bg-gray-100 text-gray-600 text-xs font-semibold px-2.5 py-0.5 rounded-full">
          {{ entry.task.estimated_minutes }}min
        </span>
      </div>

      <div class="flex items-center gap-2 w-full md:w-auto justify-between md:justify-start">
        <div class="flex gap-2">
          <template v-if="entry.task.status === 'pending'">
            <button @click="emit('start', entry.task.id)" class="bg-blue-500 hover:bg-blue-600 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors">
              Start
            </button>
          </template>
          <template v-if="entry.task.status === 'in_progress'">
            <button @click="showCompleteForm = !showCompleteForm" class="bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors">
              Complete
            </button>
            <button @click="showDelayForm = !showDelayForm" class="bg-amber-400 hover:bg-amber-500 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors">
              Delay
            </button>
          </template>
        </div>
        <button @click="emit('delete', entry.task.id)" class="text-gray-300 hover:text-red-500 transition-colors text-lg font-bold leading-none px-1">
          ×
        </button>
      </div>
    </div>

    <div v-if="showCompleteForm" class="flex gap-2 items-center px-4 pb-3 pt-2 border-t border-gray-100">
      <span class="text-xs text-gray-500">Actual time:</span>
      <input v-model.number="actualMinutes" type="number" min="1" class="border rounded-lg px-2 py-1 w-20 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-400" />
      <span class="text-xs text-gray-400">min</span>
      <button @click="handleComplete" class="bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors">
        Confirm
      </button>
    </div>

    <div v-if="showDelayForm" class="flex gap-2 items-center px-4 pb-3 pt-2 border-t border-gray-100">
      <span class="text-xs text-gray-500">Extra time:</span>
      <input v-model.number="extraMinutes" type="number" min="1" class="border rounded-lg px-2 py-1 w-20 text-xs focus:outline-none focus:ring-2 focus:ring-amber-400" />
      <span class="text-xs text-gray-400">min</span>
      <button @click="handleDelay" class="bg-amber-400 hover:bg-amber-500 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors">
        Confirm
      </button>
    </div>

    <p v-if="error" class="px-4 pb-3 text-xs text-red-600 font-medium">{{ error }}</p>
  </div>
</template>

<style scoped></style>
