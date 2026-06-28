import type { AppEvents } from '../shared/messages/appEvents'
import type { MessageBus } from '../shared/messages/messageBus'

export interface PluginContext {
  messages: MessageBus<AppEvents>
}

export interface RecoilStudioPlugin {
  id: string
  version: string
  activate(ctx: PluginContext): void | Promise<void>
  deactivate?(ctx: PluginContext): void | Promise<void>
}

export class PluginManager {
  private plugins = new Map<string, RecoilStudioPlugin>()
  private readonly ctx: PluginContext

  constructor(ctx: PluginContext) {
    this.ctx = ctx
  }

  async register(plugin: RecoilStudioPlugin) {
    if (this.plugins.has(plugin.id)) {
      throw new Error(`Plugin already registered: ${plugin.id}`)
    }

    await plugin.activate(this.ctx)
    this.plugins.set(plugin.id, plugin)
  }

  async unregister(pluginId: string) {
    const plugin = this.plugins.get(pluginId)
    if (!plugin) return

    await plugin.deactivate?.(this.ctx)
    this.plugins.delete(pluginId)
  }

  has(pluginId: string) {
    return this.plugins.has(pluginId)
  }

  list() {
    return [...this.plugins.values()]
  }
}
