import { describe, expect, it, vi } from 'vitest'
import { MessageBus } from '../shared/messages/messageBus'
import type { AppEvents } from '../shared/messages/appEvents'
import { PluginManager, type RecoilStudioPlugin } from './pluginManager'

describe('PluginManager', () => {
  it('activates and lists registered plugins', async () => {
    const messages = new MessageBus<AppEvents>()
    const manager = new PluginManager({ messages })
    const plugin: RecoilStudioPlugin = {
      id: 'test-plugin',
      version: '1.0.0',
      activate: vi.fn(),
    }

    await manager.register(plugin)

    expect(plugin.activate).toHaveBeenCalledWith({ messages })
    expect(manager.has('test-plugin')).toBe(true)
    expect(manager.list()).toEqual([plugin])
  })

  it('rejects duplicate plugin ids', async () => {
    const manager = new PluginManager({ messages: new MessageBus<AppEvents>() })
    const plugin: RecoilStudioPlugin = {
      id: 'duplicate',
      version: '1.0.0',
      activate: vi.fn(),
    }

    await manager.register(plugin)
    await expect(manager.register(plugin)).rejects.toThrow('Plugin already registered')
  })

  it('deactivates plugins before unregistering', async () => {
    const manager = new PluginManager({ messages: new MessageBus<AppEvents>() })
    const plugin: RecoilStudioPlugin = {
      id: 'disposable',
      version: '1.0.0',
      activate: vi.fn(),
      deactivate: vi.fn(),
    }

    await manager.register(plugin)
    await manager.unregister(plugin.id)

    expect(plugin.deactivate).toHaveBeenCalled()
    expect(manager.has(plugin.id)).toBe(false)
  })
})
