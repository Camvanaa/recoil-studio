<script setup lang="ts">
import { ref } from 'vue'
import { api, type Point, type RecoilData } from '../api'

const emit = defineEmits<{
  detected: [{
    points: Point[]
    pattern: RecoilData[]
    imageUrl: string
    width: number
    height: number
  }]
  imported: [{ pattern: RecoilData[] }]
}>()

const activeTab = ref<'image' | 'data'>('image')
const isDragging = ref(false)
const isLoading = ref(false)
const error = ref('')
const scaleX = ref(1.0)
const scaleY = ref(1.0)
const minDist = ref(5)
const dataInput = ref('')

// 预览状态
const previewMode = ref(false)
const previewPoints = ref<Point[]>([])
const previewPattern = ref<RecoilData[]>([])
const previewImageUrl = ref('')
const previewWidth = ref(0)
const previewHeight = ref(0)

async function handleFile(file: File) {
  if (!file.type.startsWith('image/')) {
    error.value = '请上传图片文件'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    const result = await api.detectPattern(file, scaleX.value, scaleY.value, minDist.value)
    
    if (result.success) {
      previewPoints.value = result.points
      previewPattern.value = result.pattern
      previewImageUrl.value = URL.createObjectURL(file)
      previewWidth.value = result.image_width
      previewHeight.value = result.image_height
      previewMode.value = true
    } else {
      error.value = result.message
    }
  } catch (e: any) {
    error.value = e.message || '识别失败'
  } finally {
    isLoading.value = false
  }
}

function confirmDetection() {
  emit('detected', {
    points: previewPoints.value,
    pattern: previewPattern.value,
    imageUrl: previewImageUrl.value,
    width: previewWidth.value,
    height: previewHeight.value
  })
}

function cancelPreview() {
  previewMode.value = false
  previewPoints.value = []
  previewPattern.value = []
  previewImageUrl.value = ''
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file) handleFile(file)
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) handleFile(file)
}

function parseDataInput() {
  error.value = ''
  
  try {
    const text = dataInput.value.trim()
    let data: RecoilData[] = []
    
    // 尝试解析 JSON 格式
    if (text.startsWith('[') || text.startsWith('{')) {
      const parsed = JSON.parse(text)
      if (Array.isArray(parsed)) {
        data = parsed.map(item => ({
          y: Number(item.y) || 0,
          x: Number(item.x) || 0
        }))
      }
    } else {
      // 尝试解析 Lua 格式或简单格式
      // 匹配 {y=数字, x=数字} 或 数字,数字
      const luaPattern = /\{y\s*=\s*([-\d.]+)\s*,\s*x\s*=\s*([-\d.]+)\}/g
      const simplePattern = /([-\d.]+)\s*[,\s]\s*([-\d.]+)/g
      
      let match
      while ((match = luaPattern.exec(text)) !== null) {
        if (match[1] && match[2]) {
          data.push({ y: parseFloat(match[1]), x: parseFloat(match[2]) })
        }
      }
      
      if (data.length === 0) {
        while ((match = simplePattern.exec(text)) !== null) {
          if (match[1] && match[2]) {
            data.push({ y: parseFloat(match[1]), x: parseFloat(match[2]) })
          }
        }
      }
    }
    
    if (data.length === 0) {
      error.value = '无法解析数据，请检查格式'
      return
    }
    
    emit('imported', { pattern: data })
    
  } catch (e: any) {
    error.value = '解析失败: ' + e.message
  }
}
</script>

<template>
  <div class="upload-container">
    <!-- 预览模式 -->
    <div v-if="previewMode" class="preview-mode">
      <div class="preview-header">
        <h3>识别结果预览</h3>
        <span class="preview-info">识别到 {{ previewPoints.length }} 个弹道点</span>
      </div>
      
      <div class="preview-content">
        <div class="preview-image">
          <img :src="previewImageUrl" alt="Preview" />
          <svg class="preview-overlay" :viewBox="`0 0 ${previewWidth} ${previewHeight}`">
            <polyline
              :points="previewPoints.map(p => `${p.x},${p.y}`).join(' ')"
              fill="none"
              stroke="rgba(102, 126, 234, 0.6)"
              stroke-width="2"
            />
            <circle
              v-for="(point, i) in previewPoints"
              :key="i"
              :cx="point.x"
              :cy="point.y"
              r="5"
              fill="#667eea"
              stroke="#fff"
              stroke-width="1"
            />
          </svg>
        </div>
        
        <div class="preview-data">
          <h4>弹道数据 ({{ previewPattern.length }} 发)</h4>
          <div class="data-list">
            <div v-for="(p, i) in previewPattern.slice(0, 10)" :key="i" class="data-item">
              <span class="num">#{{ i + 1 }}</span>
              <span>Y: {{ p.y.toFixed(2) }}</span>
              <span>X: {{ p.x.toFixed(2) }}</span>
            </div>
            <div v-if="previewPattern.length > 10" class="data-more">
              ... 还有 {{ previewPattern.length - 10 }} 发
            </div>
          </div>
        </div>
      </div>
      
      <div class="preview-actions">
        <button class="btn btn-secondary" @click="cancelPreview">重新上传</button>
        <button class="btn btn-primary" @click="confirmDetection">确认并编辑</button>
      </div>
    </div>
    
    <!-- 上传模式 -->
    <div v-else>
      <div class="tabs">
        <button 
          :class="['tab', { active: activeTab === 'image' }]" 
          @click="activeTab = 'image'"
        >
          上传弹道图
        </button>
        <button 
          :class="['tab', { active: activeTab === 'data' }]" 
          @click="activeTab = 'data'"
        >
          导入弹道数据
        </button>
      </div>
      
      <!-- 图片上传 -->
      <div v-if="activeTab === 'image'" class="tab-content">
        <div class="params">
          <div class="param">
            <label>X缩放</label>
            <input type="number" v-model.number="scaleX" step="0.1" min="0.1" max="10" />
          </div>
          <div class="param">
            <label>Y缩放</label>
            <input type="number" v-model.number="scaleY" step="0.1" min="0.1" max="10" />
          </div>
          <div class="param">
            <label>点间距</label>
            <input type="number" v-model.number="minDist" min="1" max="20" />
          </div>
        </div>

        <div
          :class="['drop-zone', { dragging: isDragging, loading: isLoading }]"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
          @click="($refs.fileInput as HTMLInputElement).click()"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            hidden
            @change="handleFileInput"
          />
          
          <div v-if="isLoading" class="loading">
            <div class="spinner"></div>
            <p>正在识别弹道...</p>
          </div>
          
          <div v-else class="placeholder">
            <div class="icon">📁</div>
            <p>拖拽弹道图到这里</p>
            <p class="sub">或点击选择文件</p>
          </div>
        </div>
      </div>
      
      <!-- 数据导入 -->
      <div v-if="activeTab === 'data'" class="tab-content">
        <div class="data-import">
          <p class="hint">支持以下格式：</p>
          <ul class="format-list">
            <li>JSON: <code>[{"y": 10, "x": 2}, ...]</code></li>
            <li>Lua: <code>{y=10, x=2}, {y=8, x=-1}, ...</code></li>
            <li>简单: <code>10, 2</code> (每行一发，Y和X用逗号分隔)</li>
          </ul>
          
          <textarea 
            v-model="dataInput" 
            placeholder="粘贴弹道数据..."
            rows="10"
          ></textarea>
          
          <button class="btn btn-primary" @click="parseDataInput" :disabled="!dataInput.trim()">
            导入数据
          </button>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.upload-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tabs {
  display: flex;
  gap: 10px;
  border-bottom: 1px solid #333;
  padding-bottom: 10px;
}

.tab {
  padding: 10px 20px;
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 1rem;
  border-radius: 6px 6px 0 0;
  transition: all 0.2s;
}

.tab:hover {
  color: #fff;
  background: rgba(255,255,255,0.05);
}

.tab.active {
  color: #fff;
  background: rgba(102, 126, 234, 0.2);
  border-bottom: 2px solid #667eea;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.params {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.param {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.param label {
  font-size: 0.85rem;
  color: #999;
}

.param input {
  width: 80px;
  padding: 8px;
  border: 1px solid #333;
  border-radius: 6px;
  background: #1a1a2e;
  color: #fff;
  text-align: center;
}

.drop-zone {
  border: 2px dashed #444;
  border-radius: 12px;
  padding: 50px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.drop-zone:hover,
.drop-zone.dragging {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.drop-zone.loading {
  pointer-events: none;
}

.placeholder .icon {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.placeholder .sub {
  font-size: 0.85rem;
  color: #666;
  margin-top: 5px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #333;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 数据导入 */
.data-import {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.hint {
  color: #999;
  font-size: 0.9rem;
}

.format-list {
  margin: 0;
  padding-left: 20px;
  color: #888;
  font-size: 0.85rem;
}

.format-list code {
  background: #1a1a2e;
  padding: 2px 6px;
  border-radius: 4px;
  color: #a8e6cf;
}

textarea {
  width: 100%;
  padding: 15px;
  border: 1px solid #333;
  border-radius: 8px;
  background: #1a1a2e;
  color: #fff;
  font-family: 'Consolas', monospace;
  font-size: 0.9rem;
  resize: vertical;
}

/* 预览模式 */
.preview-mode {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-header h3 {
  color: #667eea;
}

.preview-info {
  color: #999;
}

.preview-content {
  display: grid;
  grid-template-columns: 1fr 250px;
  gap: 20px;
}

.preview-image {
  position: relative;
  background: #0a0a1a;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  padding: 20px;
}

.preview-image img {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
}

.preview-overlay {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  max-width: calc(100% - 40px);
  max-height: 400px;
  pointer-events: none;
}

.preview-data {
  background: #1a1a2e;
  border-radius: 8px;
  padding: 15px;
}

.preview-data h4 {
  margin-bottom: 10px;
  color: #999;
  font-size: 0.9rem;
}

.data-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-height: 300px;
  overflow-y: auto;
}

.data-item {
  display: flex;
  gap: 10px;
  padding: 5px 8px;
  background: #16213e;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: monospace;
}

.data-item .num {
  color: #667eea;
  min-width: 25px;
}

.data-more {
  text-align: center;
  color: #666;
  font-size: 0.85rem;
  padding: 10px;
}

.preview-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

/* 按钮 */
.btn {
  padding: 12px 30px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #333;
  color: #fff;
}

.btn-secondary:hover {
  background: #444;
}

.error {
  background: rgba(255, 100, 100, 0.2);
  border: 1px solid #f66;
  color: #f66;
  padding: 10px;
  border-radius: 6px;
  text-align: center;
}

@media (max-width: 700px) {
  .preview-content {
    grid-template-columns: 1fr;
  }
}
</style>
