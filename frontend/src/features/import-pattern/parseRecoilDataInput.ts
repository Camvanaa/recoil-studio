import type { RecoilData } from '../../api'
import { ParserRegistry, type RecoilDataParser } from './parserRegistry'

export const jsonRecoilParser: RecoilDataParser = {
  id: 'json-recoil',
  label: 'JSON recoil array',
  canParse: (input) => input.startsWith('[') || input.startsWith('{'),
  parse: parseJsonRecoilData,
}

export const luaRecoilParser: RecoilDataParser = {
  id: 'lua-recoil',
  label: 'Lua recoil table',
  canParse: (input) => /\{y\s*=/.test(input),
  parse: parseLuaRecoilData,
}

export const simpleRecoilParser: RecoilDataParser = {
  id: 'simple-recoil',
  label: 'Simple delimited recoil rows',
  canParse: () => true,
  parse: parseSimpleRecoilData,
}

export function createDefaultParserRegistry() {
  const registry = new ParserRegistry()
  registry.register(luaRecoilParser)
  registry.register(jsonRecoilParser)
  registry.register(simpleRecoilParser)
  return registry
}

const defaultParserRegistry = createDefaultParserRegistry()

export function parseRecoilDataInput(input: string): RecoilData[] {
  return defaultParserRegistry.parse(input)
}

function parseJsonRecoilData(text: string): RecoilData[] {
  const parsed: unknown = JSON.parse(text)
  if (!Array.isArray(parsed)) return []

  return parsed.map((item) => {
    if (!isRecord(item)) return { y: 0, x: 0 }

    return {
      y: Number(item.y) || 0,
      x: Number(item.x) || 0,
    }
  })
}

function parseLuaRecoilData(text: string): RecoilData[] {
  const data: RecoilData[] = []
  const luaPattern = /\{y\s*=\s*([-\d.]+)\s*,\s*x\s*=\s*([-\d.]+)\}/g
  let match: RegExpExecArray | null

  while ((match = luaPattern.exec(text)) !== null) {
    const [, y, x] = match
    if (y !== undefined && x !== undefined) {
      data.push({ y: parseFloat(y), x: parseFloat(x) })
    }
  }

  return data
}

function parseSimpleRecoilData(text: string): RecoilData[] {
  const data: RecoilData[] = []
  const simplePattern = /([-\d.]+)\s*[,\s]\s*([-\d.]+)/g
  let match: RegExpExecArray | null

  while ((match = simplePattern.exec(text)) !== null) {
    const [, y, x] = match
    if (y !== undefined && x !== undefined) {
      data.push({ y: parseFloat(y), x: parseFloat(x) })
    }
  }

  return data
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
