import type { StudioPatch } from '../../api'

export interface PatchTemplate {
  id: string
  label: string
  patch: StudioPatch
}

export const patchTemplates: PatchTemplate[] = [
  {
    id: 'scale-pattern-up',
    label: '垂直 +10%',
    patch: {
      id: 'scale-pattern-up',
      title: 'Increase vertical recoil by 10%',
      operations: [{ type: 'transform-pattern', target: 'pattern', scale_y: 1.1, scale_x: 1 }],
    },
  },
  {
    id: 'scale-pattern-down',
    label: '垂直 -10%',
    patch: {
      id: 'scale-pattern-down',
      title: 'Decrease vertical recoil by 10%',
      operations: [{ type: 'transform-pattern', target: 'pattern', scale_y: 0.9, scale_x: 1 }],
    },
  },
  {
    id: 'mouse-sens',
    label: '鼠标灵敏度 5',
    patch: {
      id: 'set-mouse-sens',
      title: 'Set mouse sensitivity',
      operations: [{ type: 'set-field', target: 'sensitivity', path: 'mouse_sens', value: 5 }],
    },
  },
]

export function stringifyPatchTemplate(template: PatchTemplate) {
  return JSON.stringify(template.patch, null, 2)
}
