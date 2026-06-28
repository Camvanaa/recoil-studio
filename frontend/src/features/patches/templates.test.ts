import { describe, expect, it } from 'vitest'
import { patchTemplates, stringifyPatchTemplate } from './templates'

describe('patchTemplates', () => {
  it('contains valid patch json templates', () => {
    for (const template of patchTemplates) {
      const parsed = JSON.parse(stringifyPatchTemplate(template))

      expect(parsed.id).toBe(template.patch.id)
      expect(Array.isArray(parsed.operations)).toBe(true)
    }
  })
})
