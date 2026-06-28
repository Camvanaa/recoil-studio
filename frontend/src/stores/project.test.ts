import { setActivePinia, createPinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { useProjectStore } from './project'

describe('project store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('imports recoil data as editable points', () => {
    const project = useProjectStore()

    project.importPattern({ pattern: [{ y: 10, x: 2 }] })

    expect(project.pattern).toEqual([{ y: 10, x: 2 }])
    expect(project.points).toEqual([
      { x: 100, y: 400 },
      { x: 96, y: 380 },
    ])
    expect(project.imageWidth).toBe(300)
    expect(project.imageHeight).toBe(500)
  })

  it('exposes and applies project state for patch manager', () => {
    const project = useProjectStore()
    project.importPattern({ pattern: [{ y: 10, x: 2 }] })

    expect(project.getProjectState()).toEqual({
      pattern: [{ y: 10, x: 2 }],
      guns: [],
      sensitivity: project.sensitivity,
    })

    project.applyProjectState({
      pattern: [{ y: 20, x: 1 }],
      guns: [],
      sensitivity: { ...project.sensitivity, mouse_sens: 3.5 },
    })

    expect(project.pattern).toEqual([{ y: 20, x: 1 }])
    expect(project.sensitivity.mouse_sens).toBe(3.5)
  })
})
