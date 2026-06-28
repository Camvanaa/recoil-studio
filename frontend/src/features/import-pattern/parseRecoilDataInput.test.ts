import { describe, expect, it } from 'vitest'
import { parseRecoilDataInput } from './parseRecoilDataInput'

describe('parseRecoilDataInput', () => {
  it('parses JSON recoil arrays', () => {
    expect(parseRecoilDataInput('[{"y": 10, "x": -2}, {"y": "5.5", "x": 0}]')).toEqual([
      { y: 10, x: -2 },
      { y: 5.5, x: 0 },
    ])
  })

  it('parses Lua table entries', () => {
    expect(parseRecoilDataInput('{y=10, x=2}, {y=8.5, x=-1.25}')).toEqual([
      { y: 10, x: 2 },
      { y: 8.5, x: -1.25 },
    ])
  })

  it('parses simple comma separated entries', () => {
    expect(parseRecoilDataInput('10, 2\n8.5, -1.25')).toEqual([
      { y: 10, x: 2 },
      { y: 8.5, x: -1.25 },
    ])
  })

  it('returns an empty array for unsupported object JSON', () => {
    expect(parseRecoilDataInput('{"pattern": []}')).toEqual([])
  })

  it('throws invalid JSON errors to the caller', () => {
    expect(() => parseRecoilDataInput('[{"y": 10]')).toThrow()
  })
})
