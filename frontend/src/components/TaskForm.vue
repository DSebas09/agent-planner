<script setup lang="ts">
import { reactive } from 'vue'
import type { TaskCreate, Priority, EnergyLevel } from '../types'

interface Props {
  error?: string | null
}

defineProps<Props>()

const emit = defineEmits<{
  submit: [payload: TaskCreate]
}>()

const form = reactive({
  title: '',
  priority: 'medium' as Priority,
  energy_required: 'medium' as EnergyLevel,
  estimated_minutes: 30,
  deadline: '',
})

const priorities: Priority[] = ['high', 'medium', 'low']
const energyLevels: EnergyLevel[] = ['high', 'medium', 'low']

const priorityActive: Record<Priority, string> = {
  high:   'bg-red-500 border-red-500 text-white',
  medium: 'bg-amber-400 border-amber-400 text-white',
  low:    'bg-emerald-500 border-emerald-500 text-white',
}

const energyActive: Record<EnergyLevel, string> = {
  high:   'bg-violet-500 border-violet-500 text-white',
  medium: 'bg-blue-500 border-blue-500 text-white',
  low:    'bg-teal-500 border-teal-500 text-white',
}

function resetForm() {
  form.title = ''
  form.priority = 'medium'
  form.energy_required = 'medium'
  form.estimated_minutes = 30
  form.deadline = ''
}

function handleSubmit() {
  emit('submit', {
    title: form.title,
    priority: form.priority,
    energy_required: form.energy_required,
    estimated_minutes: form.estimated_minutes,
    deadline: form.deadline ? new Date(form.deadline).toISOString() : null,
  })
  resetForm()
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col gap-4">
    <h2 class="font-bold text-gray-800 text-base">New task</h2>

    <input
      v-model="form.title"
      type="text"
      placeholder="What needs to get done?"
      required
      class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
    />

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="flex flex-col gap-1.5">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Priority</span>
        <div class="flex gap-1.5">
          <button
            v-for="p in priorities"
            :key="p"
            type="button"
            @click="form.priority = p"
            :class="form.priority === p ? priorityActive[p] : 'bg-white border-gray-200 text-gray-400 hover:border-gray-300'"
            class="flex-1 py-1.5 text-xs font-bold rounded-full border-2 capitalize transition-colors"
          >
            {{ p }}
          </button>
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Energy</span>
        <div class="flex gap-1.5">
          <button
            v-for="e in energyLevels"
            :key="e"
            type="button"
            @click="form.energy_required = e"
            :class="form.energy_required === e ? energyActive[e] : 'bg-white border-gray-200 text-gray-400 hover:border-gray-300'"
            class="flex-1 py-1.5 text-xs font-bold rounded-full border-2 capitalize transition-colors"
          >
            {{ e }}
          </button>
        </div>
      </div>
    </div>

    <div class="flex flex-col sm:flex-row gap-3">
      <div class="flex flex-col gap-1.5">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Duration</span>
        <div class="flex items-center gap-1.5">
          <input
            v-model.number="form.estimated_minutes"
            type="number"
            min="1"
            required
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <span class="text-xs text-gray-400">min</span>
        </div>
      </div>

      <div class="flex flex-col gap-1.5 flex-1">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Deadline</span>
        <input
          v-model="form.deadline"
          type="datetime-local"
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>
    </div>

    <button
      type="submit"
      class="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm"
    >
      + Add task
    </button>

    <p v-if="error" class="text-xs text-red-600 font-medium">{{ error }}</p>
  </form>
</template>

<style scoped></style>
