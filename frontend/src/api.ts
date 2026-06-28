import axios from 'axios'

const API_BASE = '/api'

export interface Point {
  x: number
  y: number
}

export interface RecoilData {
  y: number
  x: number
}

export interface PatternDetectResponse {
  success: boolean
  message: string
  points: Point[]
  pattern: RecoilData[]
  image_width: number
  image_height: number
   shot_count: number
   recoil_step_count: number
   sample_count: number
   skipped_sample_count: number
   detection_mode: 'green' | 'target' | 'manual'
}

export interface GunConfig {
  name: string
  rpm: number
  vertical_mul: number
  horizontal_mul: number
  pattern: RecoilData[]
}

export interface LuaGenerateResponse {
  success: boolean
  message: string
  lua_code: string
}

export const api = {
  async detectPattern(
    file: File,
    scaleX: number = 1.0,
    scaleY: number = 1.0,
    minDist: number = 5,
    detectionMode: 'auto' | 'green' | 'target' = 'auto'
  ): Promise<PatternDetectResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('scale_x', scaleX.toString())
    formData.append('scale_y', scaleY.toString())
    formData.append('min_dist', minDist.toString())
    formData.append('detection_mode', detectionMode)

    const response = await axios.post<PatternDetectResponse>(
      `${API_BASE}/pattern/detect`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  },

  async detectPatternBatch(
    files: File[],
    scaleX: number = 1.0,
    scaleY: number = 1.0,
    minDist: number = 5,
    detectionMode: 'auto' | 'green' | 'target' = 'target'
  ): Promise<PatternDetectResponse> {
    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }
    formData.append('scale_x', scaleX.toString())
    formData.append('scale_y', scaleY.toString())
    formData.append('min_dist', minDist.toString())
    formData.append('detection_mode', detectionMode)

    const response = await axios.post<PatternDetectResponse>(
      `${API_BASE}/pattern/detect-batch`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  },

  async recalculatePattern(
    points: Point[],
    scaleX: number = 1.0,
    scaleY: number = 1.0
  ): Promise<PatternDetectResponse> {
    const response = await axios.post<PatternDetectResponse>(
      `${API_BASE}/pattern/recalculate`,
      {
        points,
        scale_x: scaleX,
        scale_y: scaleY
      }
    )
    return response.data
  },

  async generateLua(guns: GunConfig[]): Promise<LuaGenerateResponse> {
    const response = await axios.post<LuaGenerateResponse>(
      `${API_BASE}/lua/generate`,
      { guns }
    )
    return response.data
  },

  async downloadLua(guns: GunConfig[]): Promise<Blob> {
    const response = await axios.post(
      `${API_BASE}/lua/download`,
      { guns },
      { responseType: 'blob' }
    )
    return response.data
  }
}
