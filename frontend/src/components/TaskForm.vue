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
  <form @submit.prevent="handleSubmit" class="flex flex-col gap-3">
    <input
      v-model="form.title"
      type="text"
      placeholder="Task title"
      required
      class="border rounded px-3 py-2"
    />

    <div class="flex gap-2">
      <select v-model="form.priority" class="border rounded px-3 py-2 flex-1">
        <option value="high">High priority</option>
        <option value="medium">Medium priority</option>
        <option value="low">Low priority</option>
      </select>

      <select v-model="form.energy_required" class="border rounded px-3 py-2 flex-1">
        <option value="high">High energy</option>
        <option value="medium">Medium energy</option>
        <option value="low">Low energy</option>
      </select>
    </div>

    <div class="flex gap-2">
      <input
        v-model.number="form.estimated_minutes"
        type="number"
        min="1"
        placeholder="Minutes"
        required
        class="border rounded px-3 py-2 w-32"
      />

      <input
        v-model="form.deadline"
        type="datetime-local"
        class="border rounded px-3 py-2 flex-1"
      />
    </div>

    <button type="submit" class="bg-blue-600 text-white rounded px-4 py-2 hover:bg-blue-700">
      Add task
    </button>

    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
  </form>
</template>

<style scoped></style>
