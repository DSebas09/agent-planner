import type { Ref } from 'vue'

export async function withLoading<T>(
  isLoading: Ref<boolean>,
  error: Ref<string | null>,
  fn: () => Promise<T>
): Promise<T | null> {
  isLoading.value = true
  error.value = null
  try {
    return await fn()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
    return null
  } finally {
    isLoading.value = false
  }
}
