import { describe, expect, it } from 'vitest'
import { createApp, defineComponent } from 'vue'
import { installRuntime, useRuntime } from './runtimeContext'

describe('runtimeContext', () => {
  it('installs runtime into a Vue app', () => {
    const app = createApp({})

    const runtime = installRuntime(app)

    expect(runtime.messages).toBeDefined()
    expect(runtime.plugins).toBeDefined()
  })

  it('throws when runtime is not provided', () => {
    const component = defineComponent({
      setup() {
        useRuntime()
        return () => null
      },
    })

    expect(component.setup).toThrow('Runtime has not been installed')
  })
})
