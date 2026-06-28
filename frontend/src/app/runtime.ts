import { MessageBus } from '../shared/messages/messageBus'
import type { AppEvents } from '../shared/messages/appEvents'
import { PluginManager } from '../plugins/pluginManager'

export function createRuntime() {
  const messages = new MessageBus<AppEvents>()
  const plugins = new PluginManager({ messages })

  return { messages, plugins }
}
