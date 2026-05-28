<script setup lang="ts">
import { onMounted } from 'vue'
import TaskForm from '../components/TaskForm.vue'
import TaskCard from '../components/TaskCard.vue'
import AgentLog from '../components/AgentLog.vue'
import { useTasks } from '../composables/useTasks'
import { usePlan } from '../composables/usePlan'
import { useLogs } from '../composables/useLogs'
import type { TaskCreate } from '../types'

const { createTask, startTask, completeTask, reportDelay, deleteTask } = useTasks()
const { plan, startPolling } = usePlan()
const { logs } = useLogs()

onMounted(() => startPolling())
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Day Planner</h1>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <div class="lg:col-span-2 flex flex-col gap-4">
        <TaskForm @submit="(payload: TaskCreate) => createTask(payload)" />

        <p v-if="plan.length === 0" class="text-gray-400 text-sm text-center py-8">
          No tasks planned for today.
        </p>

        <template v-for="entry in plan" :key="entry.task.id">
          <TaskCard
            :entry="entry"
            @start="startTask"
            @complete="completeTask"
            @delay="reportDelay"
            @delete="deleteTask"
          />
        </template>
      </div>

      <div class="bg-white border rounded-lg p-4 h-fit sticky top-6">
        <h2 class="font-semibold text-gray-700 mb-3">Agent Log</h2>
        <AgentLog :logs="logs" />
      </div>

    </div>
  </div>
</template>

<style scoped></style>
