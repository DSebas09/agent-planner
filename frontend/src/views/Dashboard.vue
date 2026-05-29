<script setup lang="ts">
import { onMounted, ref } from 'vue'
import TaskForm from '../components/TaskForm.vue'
import TaskCard from '../components/TaskCard.vue'
import AgentLog from '../components/AgentLog.vue'
import { useTasks } from '../composables/useTasks'
import { usePlan } from '../composables/usePlan'
import { useLogs } from '../composables/useLogs'
import type { TaskCreate } from '../types'

const { createTask, startTask, completeTask, reportDelay, deleteTask, error: actionError } = useTasks()
const { plan, startPolling } = usePlan()
const { logs } = useLogs()

const showForm = ref(false)
const formError = ref<string | null>(null)
const errorTaskId = ref<number | null>(null)

onMounted(() => startPolling())

async function handleCreate(payload: TaskCreate) {
  formError.value = null
  await createTask(payload)
  formError.value = actionError.value
  if (!formError.value) showForm.value = false
}

async function handleTaskAction(id: number, fn: () => Promise<unknown>) {
  errorTaskId.value = null
  await fn()
  if (actionError.value) errorTaskId.value = id
}
</script>

<template>
  <div class="h-screen bg-gray-50 flex flex-col overflow-hidden">

    <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 class="text-lg font-bold text-gray-900">Agent Planner</h1>
        <p class="text-xs text-gray-400">{{ new Date().toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' }) }}</p>
      </div>
      <button
        @click="showForm = !showForm"
        :class="showForm ? 'bg-gray-100 text-gray-600' : 'bg-blue-500 text-white hover:bg-blue-600'"
        class="text-sm font-semibold px-4 py-2 rounded-full transition-colors"
      >
        {{ showForm ? '✕ Cancel' : '+ New Task' }}
      </button>
    </header>

    <div v-if="showForm" class="bg-white border-b border-gray-200 px-6 py-5">
      <div class="max-w-2xl mx-auto">
        <TaskForm :error="formError" @submit="handleCreate" />
      </div>
    </div>

    <main class="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-3 w-full">
      <p v-if="plan.length === 0" class="text-gray-400 text-sm text-center py-12">
        No tasks planned for today. Add one to get started.
      </p>

      <template v-for="entry in plan" :key="entry.task.id">
        <TaskCard
          :entry="entry"
          :error="errorTaskId === entry.task.id ? actionError : null"
          @start="(id) => handleTaskAction(id, () => startTask(id))"
          @complete="(id, mins) => handleTaskAction(id, () => completeTask(id, mins))"
          @delay="(id, mins) => handleTaskAction(id, () => reportDelay(id, mins))"
          @delete="(id) => handleTaskAction(id, () => deleteTask(id))"
        />
      </template>
    </main>

    <footer class="px-6 pb-6 w-full">
      <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Agent Log</p>
      <AgentLog :logs="logs" />
    </footer>

  </div>
</template>

<style scoped></style>
