export type EventMap = Record<string, unknown>
export type EventHandler<Payload> = (payload: Payload) => void

export class MessageBus<Events extends EventMap> {
  private handlers = new Map<keyof Events, Set<EventHandler<Events[keyof Events]>>>()

  on<EventName extends keyof Events>(
    eventName: EventName,
    handler: EventHandler<Events[EventName]>,
  ): () => void {
    const handlers = this.handlers.get(eventName) ?? new Set()
    handlers.add(handler as EventHandler<Events[keyof Events]>)
    this.handlers.set(eventName, handlers)

    return () => this.off(eventName, handler)
  }

  off<EventName extends keyof Events>(eventName: EventName, handler: EventHandler<Events[EventName]>) {
    this.handlers.get(eventName)?.delete(handler as EventHandler<Events[keyof Events]>)
  }

  emit<EventName extends keyof Events>(eventName: EventName, payload: Events[EventName]) {
    for (const handler of this.handlers.get(eventName) ?? []) {
      handler(payload)
    }
  }

  clear() {
    this.handlers.clear()
  }
}
