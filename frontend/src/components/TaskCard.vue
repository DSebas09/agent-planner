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
    class="border-l-4 rounded-lg p-4 flex flex-col gap-3 shadow-sm border border-gray-100"
  >
    <div class="flex items-center justify-between">
      <span class="text-xs font-mono text-gray-400">
        #{{ entry.position }} · {{ formatTime(entry.scheduled_start) }} — {{ formatTime(entry.scheduled_end) }}
      </span>
      <span
        v-if="deadlineLabel"
        :class="deadlineClass"
        class="text-xs font-semibold px-2 py-0.5 rounded-full"
      >
        {{ deadlineLabel }}
      </span>
    </div>

    <p class="font-bold text-gray-900 text-base leading-snug">{{ entry.task.title }}</p>

    <div class="flex gap-1.5 flex-wrap">
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

    <div class="flex items-center gap-2 pt-1 border-t border-gray-100">
      <template v-if="entry.task.status === 'pending'">
        <button
          @click="emit('start', entry.task.id)"
          class="bg-blue-500 hover:bg-blue-600 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors"
        >
          Start
        </button>
      </template>

      <template v-if="entry.task.status === 'in_progress'">
        <button
          @click="showCompleteForm = !showCompleteForm"
          class="bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors"
        >
          Complete
        </button>
        <button
          @click="showDelayForm = !showDelayForm"
          class="bg-amber-400 hover:bg-amber-500 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors"
        >
          Delay
        </button>
      </template>

      <button
        @click="emit('delete', entry.task.id)"
        class="ml-auto text-xs text-red-400 hover:text-red-600 transition-colors"
      >
        Delete
      </button>
    </div>

    <div v-if="showCompleteForm" class="flex gap-2 items-center">
      <input v-model.number="actualMinutes" type="number" min="1" class="border rounded-lg px-2 py-1 w-24 text-sm" />
      <span class="text-xs text-gray-500">actual min</span>
      <button @click="handleComplete" class="bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors">
        Confirm
      </button>
    </div>

    <div v-if="showDelayForm" class="flex gap-2 items-center">
      <input v-model.number="extraMinutes" type="number" min="1" class="border rounded-lg px-2 py-1 w-24 text-sm" />
      <span class="text-xs text-gray-500">extra min</span>
      <button @click="handleDelay" class="bg-amber-400 hover:bg-amber-500 text-white text-xs font-semibold px-3 py-1.5 rounded-full transition-colors">
        Confirm
      </button>
    </div>

    <p v-if="error" class="text-xs text-red-600 font-medium">{{ error }}</p>
  </div>
</template>

<style scoped></style>
