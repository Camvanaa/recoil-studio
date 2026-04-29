<script setup lang="ts">
import { ref } from 'vue'
import ImageUpload from './components/ImageUpload.vue'
import PatternEditor from './components/PatternEditor.vue'
import LuaPreview from './components/LuaPreview.vue'
import { defaultSensitivity, type SensitivitySettings } from './api'

interface Point {
  x: number
  y: number
}

interface RecoilData {
  y: number
  x: number
}

interface Gun {
  name: string
  rpm: number
  vertical_mul: number
  horizontal_mul: number
  scope_zoom: number
  hold_breath_coeff: number
  pattern: RecoilData[]
}

const points = ref<Point[]>([])
const pattern = ref<RecoilData[]>([])
const imageUrl = ref<string>('')
const imageWidth = ref(0)
const imageHeight = ref(0)
const guns = ref<Gun[]>([])
const currentStep = ref(1)
const sensitivity = ref<SensitivitySettings>({ ...defaultSensitivity })

function handlePatternDetected(data: {
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
  currentStep.value = 2
}

function handleDataImported(data: { pattern: RecoilData[] }) {
  // 从弹道数据生成虚拟点位（用于显示）
  let y = 400
  let x = 100
  const pts: Point[] = [{ x, y }]
  
  for (const r of data.pattern) {
    y -= r.y * 2  // 缩放用于显示
    x -= r.x * 2
    pts.push({ x, y })
  }
  
  points.value = pts
  pattern.value = data.pattern
  imageUrl.value = ''
  imageWidth.value = 300
  imageHeight.value = 500
  currentStep.value = 2
}

function handlePatternUpdated(newPattern: RecoilData[]) {
  pattern.value = newPattern
}

function handleAddGun(gun: Gun) {
  guns.value.push(gun)
  currentStep.value = 3
}

function handleRemoveGun(index: number) {
  guns.value.splice(index, 1)
  if (guns.value.length === 0) {
    currentStep.value = 2
  }
}

function handleReset() {
  points.value = []
  pattern.value = []
  imageUrl.value = ''
  currentStep.value = 1
}
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>Recoil Studio</h1>
      <p>弹道配置生成器</p>
    </header>

    <main class="main">
      <div class="steps">
        <div :class="['step', { active: currentStep >= 1, current: currentStep === 1 }]" @click="currentStep > 1 && handleReset()">
          <span class="step-number">1</span>
          <span>上传数据</span>
        </div>
        <div class="step-line" :class="{ active: currentStep >= 2 }"></div>
        <div :class="['step', { active: currentStep >= 2, current: currentStep === 2 }]">
          <span class="step-number">2</span>
          <span>编辑弹道</span>
        </div>
        <div class="step-line" :class="{ active: currentStep >= 3 }"></div>
        <div :class="['step', { active: currentStep >= 3, current: currentStep === 3 }]">
          <span class="step-number">3</span>
          <span>生成配置</span>
        </div>
      </div>

      <div class="content">
        <!-- 步骤1: 上传 -->
        <section v-if="currentStep === 1" class="section">
          <ImageUpload 
            @detected="handlePatternDetected" 
            @imported="handleDataImported"
          />
        </section>

        <!-- 步骤2: 编辑弹道 -->
        <section v-if="currentStep === 2" class="section">
          <PatternEditor
            :points="points"
            :pattern="pattern"
            :image-url="imageUrl"
            :image-width="imageWidth"
            :image-height="imageHeight"
            @update="handlePatternUpdated"
            @add-gun="handleAddGun"
            @back="handleReset"
          />
        </section>

        <!-- 步骤3: 预览和下载 -->
        <section v-if="currentStep === 3" class="section">
          <LuaPreview
            :guns="guns"
            :sensitivity="sensitivity"
            @remove="handleRemoveGun"
            @back="currentStep = 2"
            @add-more="currentStep = 1"
          />
        </section>
      </div>
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #1a1a2e;
  color: #eee;
  min-height: 100vh;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  text-align: center;
}

.header h1 {
  font-size: 1.8rem;
  margin-bottom: 5px;
}

.header p {
  opacity: 0.9;
  font-size: 0.9rem;
}

.main {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.steps {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0.4;
  transition: all 0.3s;
  cursor: default;
}

.step.active {
  opacity: 0.7;
}

.step.current {
  opacity: 1;
}

.step.active:not(.current) {
  cursor: pointer;
}

.step.active:not(.current):hover {
  opacity: 0.9;
}

.step-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
}

.step.current .step-number {
  background: #667eea;
}

.step-line {
  width: 40px;
  height: 2px;
  background: #333;
  transition: background 0.3s;
}

.step-line.active {
  background: #667eea;
}

.section {
  background: #16213e;
  border-radius: 12px;
  padding: 20px;
}
</style>
