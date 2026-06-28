import { describe, expect, it } from 'vitest'
import { ParserRegistry, type RecoilDataParser } from './parserRegistry'
import { createDefaultParserRegistry } from './parseRecoilDataInput'

describe('ParserRegistry', () => {
  it('uses the first parser that can return data', () => {
    const registry = new ParserRegistry()
    const parser: RecoilDataParser = {
      id: 'custom',
      label: 'Custom parser',
      canParse: () => true,
      parse: () => [{ y: 1, x: 2 }],
    }

    registry.register(parser)

    expect(registry.parse('anything')).toEqual([{ y: 1, x: 2 }])
  })

  it('rejects duplicate parser ids', () => {
    const registry = new ParserRegistry()
    const parser: RecoilDataParser = {
      id: 'duplicate',
      label: 'Duplicate parser',
      canParse: () => true,
      parse: () => [],
    }

    registry.register(parser)

    expect(() => registry.register(parser)).toThrow('Parser already registered')
  })

  it('registers built-in parser plugins in default registry', () => {
    const registry = createDefaultParserRegistry()

    expect(registry.list().map((parser) => parser.id)).toEqual([
      'lua-recoil',
      'json-recoil',
      'simple-recoil',
    ])
  })
})
