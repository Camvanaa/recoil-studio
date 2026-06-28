import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  defaultSensitivity,
  type GunConfig,
  type Point,
  type ProjectState,
  type RecoilData,
  type SensitivitySettings,
} from '../api'

export const useProjectStore = defineStore('project', () => {
  const points = ref<Point[]>([])
  const pattern = ref<RecoilData[]>([])
  const imageUrl = ref('')
  const imageWidth = ref(0)
  const imageHeight = ref(0)
  const guns = ref<GunConfig[]>([])
  const sensitivity = ref<SensitivitySettings>({ ...defaultSensitivity })

  function setDetectedPattern(data: {
    points: Point[]
    pattern: RecoilData[]
    imageUrl: string
    width: number
    height: number
  }) {
    points.value = data.points
    pattern.value = data.pattern
    imageUrl.value = data.imageUrl
    imageWidth.value = data.width
    imageHeight.value = data.height
  }

  function importPattern(data: { pattern: RecoilData[] }) {
    let y = 400
    let x = 100
    const importedPoints: Point[] = [{ x, y }]

    for (const recoil of data.pattern) {
      y -= recoil.y * 2
      x -= recoil.x * 2
      importedPoints.push({ x, y })
    }

    points.value = importedPoints
    pattern.value = data.pattern
    imageUrl.value = ''
    imageWidth.value = 300
    imageHeight.value = 500
  }

  function updatePattern(newPattern: RecoilData[]) {
    pattern.value = newPattern
  }

  function addGun(gun: GunConfig) {
    guns.value.push(gun)
  }

  function removeGun(index: number) {
    guns.value.splice(index, 1)
  }

  function resetPattern() {
    points.value = []
    pattern.value = []
    imageUrl.value = ''
    imageWidth.value = 0
    imageHeight.value = 0
  }

  function getProjectState(): ProjectState {
    return {
      pattern: pattern.value,
      guns: guns.value,
      sensitivity: sensitivity.value,
    }
  }

  function applyProjectState(state: ProjectState) {
    pattern.value = state.pattern
    guns.value = state.guns
    sensitivity.value = state.sensitivity
  }

  return {
    points,
    pattern,
    imageUrl,
    imageWidth,
    imageHeight,
    guns,
    sensitivity,
    setDetectedPattern,
    importPattern,
    updatePattern,
    addGun,
    removeGun,
    resetPattern,
    getProjectState,
    applyProjectState,
  }
})
