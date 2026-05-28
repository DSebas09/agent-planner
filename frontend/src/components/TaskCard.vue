<script setup lang="ts">
import { ref, computed } from 'vue'
import type { PlanEntry } from '../types'

interface Props {
  entry: PlanEntry
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

const statusColor: Record<string, string> = {
  pending:     'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed:   'bg-green-100 text-green-700',
  postponed:   'bg-yellow-100 text-yellow-700',
}

const priorityColor: Record<string, string> = {
  high:   'bg-red-100 text-red-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low:    'bg-green-100 text-green-700',
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
  <div class="border rounded-lg p-4 flex flex-col gap-2 bg-white shadow-sm">

    <div class="flex items-center justify-between text-sm text-gray-500">
      <span>{{ formatTime(entry.scheduled_start) }} — {{ formatTime(entry.scheduled_end) }}</span>
      <span v-if="deadlineLabel" class="text-red-500 font-medium">{{ deadlineLabel }}</span>
    </div>

    <p class="font-semibold text-gray-800">{{ entry.task.title }}</p>

    <div class="flex gap-2 flex-wrap text-xs font-medium">
      <span :class="priorityColor[entry.task.priority]" class="px-2 py-0.5 rounded-full">
        {{ entry.task.priority }}
      </span>
      <span class="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
        {{ entry.task.energy_required }} energy
      </span>
      <span :class="statusColor[entry.task.status]" class="px-2 py-0.5 rounded-full">
        {{ entry.task.status }}
      </span>
      <span class="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
        {{ entry.task.estimated_minutes }}min
      </span>
    </div>

    <div class="flex gap-2 mt-1">
      <template v-if="entry.task.status === 'pending'">
        <button @click="emit('start', entry.task.id)" class="text-sm text-blue-600 hover:underline">
          Start
        </button>
      </template>

      <template v-if="entry.task.status === 'in_progress'">
        <button @click="showCompleteForm = !showCompleteForm" class="text-sm text-green-600 hover:underline">
          Complete
        </button>
        <button @click="showDelayForm = !showDelayForm" class="text-sm text-yellow-600 hover:underline">
          Delay
        </button>
      </template>

      <button @click="emit('delete', entry.task.id)" class="text-sm text-red-400 hover:underline ml-auto">
        Delete
      </button>
    </div>

    <div v-if="showCompleteForm" class="flex gap-2 items-center mt-1">
      <input v-model.number="actualMinutes" type="number" min="1" class="border rounded px-2 py-1 w-24 text-sm" />
      <span class="text-sm text-gray-500">actual min</span>
      <button @click="handleComplete" class="text-sm bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700">
        Confirm
      </button>
    </div>

    <div v-if="showDelayForm" class="flex gap-2 items-center mt-1">
      <input v-model.number="extraMinutes" type="number" min="1" class="border rounded px-2 py-1 w-24 text-sm" />
      <span class="text-sm text-gray-500">extra min</span>
      <button @click="handleDelay" class="text-sm bg-yellow-600 text-white px-3 py-1 rounded hover:bg-yellow-700">
        Confirm
      </button>
    </div>

  </div>
</template>

<style scoped></style>
