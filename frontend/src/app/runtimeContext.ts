import { inject, type App, type InjectionKey } from 'vue'
import { createRuntime } from './runtime'

export type Runtime = ReturnType<typeof createRuntime>

export const runtimeKey: InjectionKey<Runtime> = Symbol('runtime')

export function installRuntime(app: App, runtime: Runtime = createRuntime()) {
  app.provide(runtimeKey, runtime)
  return runtime
}

export function useRuntime() {
  const runtime = inject(runtimeKey)
  if (!runtime) {
    throw new Error('Runtime has not been installed')
  }

  return runtime
}
