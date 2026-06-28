import type { RecoilData } from '../../api'

export interface RecoilDataParser {
  id: string
  label: string
  canParse(input: string): boolean
  parse(input: string): RecoilData[]
}

export class ParserRegistry {
  private parsers = new Map<string, RecoilDataParser>()

  register(parser: RecoilDataParser) {
    if (this.parsers.has(parser.id)) {
      throw new Error(`Parser already registered: ${parser.id}`)
    }
    this.parsers.set(parser.id, parser)
  }

  parse(input: string): RecoilData[] {
    const text = input.trim()
    if (!text) return []

    for (const parser of this.parsers.values()) {
      if (parser.canParse(text)) {
        const data = parser.parse(text)
        if (data.length > 0) return data
      }
    }

    return []
  }

  list() {
    return [...this.parsers.values()]
  }
}
