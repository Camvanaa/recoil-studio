import { describe, expect, it, vi } from 'vitest'
import { MessageBus } from './messageBus'

type TestEvents = {
  changed: { value: number }
  reset: undefined
}

describe('MessageBus', () => {
  it('emits typed payloads to subscribers', () => {
    const bus = new MessageBus<TestEvents>()
    const handler = vi.fn()

    bus.on('changed', handler)
    bus.emit('changed', { value: 42 })

    expect(handler).toHaveBeenCalledWith({ value: 42 })
  })

  it('unsubscribes handlers', () => {
    const bus = new MessageBus<TestEvents>()
    const handler = vi.fn()
    const unsubscribe = bus.on('changed', handler)

    unsubscribe()
    bus.emit('changed', { value: 42 })

    expect(handler).not.toHaveBeenCalled()
  })

  it('clears all subscriptions', () => {
    const bus = new MessageBus<TestEvents>()
    const handler = vi.fn()

    bus.on('changed', handler)
    bus.clear()
    bus.emit('changed', { value: 42 })

    expect(handler).not.toHaveBeenCalled()
  })
})
