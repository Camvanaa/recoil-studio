<script setup lang="ts">
import { ref } from 'vue'
import type { RecoilData } from '../api'

interface Gun {
  name: string
  rpm: number
  vertical_mul: number
  horizontal_mul: number
  pattern: RecoilData[]
}

const props = defineProps<{
  pattern: RecoilData[]
}>()

const emit = defineEmits<{
  add: [gun: Gun]
  back: []
}>()

const name = ref('AK-47')
const rpm = ref(600)
const verticalMul = ref(1.0)
const horizontalMul = ref(1.0)

function handleAdd() {
  if (!name.value.trim()) {
    alert('请输入枪械名称')
    return
  }
  
  if (props.pattern.length === 0) {
    alert('没有弹道数据')
    return
  }

  emit('add', {
    name: name.value.trim(),
    rpm: rpm.value,
    vertical_mul: verticalMul.value,
    horizontal_mul: horizontalMul.value,
    pattern: props.pattern
  })
}
</script>

<template>
  <div class="gun-config">
    <h3>枪械配置</h3>
    
    <div class="form">
      <div class="field">
        <label>枪械名称</label>
        <input type="text" v-model="name" placeholder="例如: AK-47" />
      </div>
      
      <div class="field">
        <label>射速 (RPM)</label>
        <input type="number" v-model.number="rpm" min="100" max="1500" />
      </div>
      
      <div class="field">
        <label>垂直倍率</label>
        <input type="number" v-model.number="verticalMul" step="0.1" min="0.1" max="5" />
      </div>
      
      <div class="field">
        <label>水平倍率</label>
        <input type="number" v-model.number="horizontalMul" step="0.1" min="0.1" max="5" />
      </div>
    </div>
    
    <div class="pattern-preview">
      <h4>弹道数据 ({{ pattern.length }} 发)</h4>
      <div class="pattern-list">
        <div v-for="(p, i) in pattern" :key="i" class="pattern-item">
          <span class="bullet-num">#{{ i + 1 }}</span>
          <span>Y: {{ p.y.toFixed(2) }}</span>
          <span>X: {{ p.x.toFixed(2) }}</span>
        </div>
      </div>
    </div>
    
    <div class="actions">
      <button class="btn btn-secondary" @click="emit('back')">
        ← 返回
      </button>
      <button class="btn btn-primary" @click="handleAdd">
        添加枪械 →
      </button>
    </div>
  </div>
</template>

<style scoped>
.gun-config {
  background: #1a1a2e;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

h3 {
  margin: 0;
  color: #667eea;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field label {
  font-size: 0.85rem;
  color: #999;
}

.field input {
  padding: 10px;
  border: 1px solid #333;
  border-radius: 6px;
  background: #16213e;
  color: #fff;
}

.pattern-preview {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.pattern-preview h4 {
  margin: 0 0 10px 0;
  font-size: 0.9rem;
  color: #999;
}

.pattern-list {
  flex: 1;
  overflow-y: auto;
  max-height: 200px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.pattern-item {
  display: flex;
  gap: 10px;
  padding: 5px 10px;
  background: #16213e;
  border-radius: 4px;
  font-size: 0.85rem;
  font-family: monospace;
}

.bullet-num {
  color: #667eea;
  min-width: 30px;
}

.actions {
  display: flex;
  gap: 10px;
}

.btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-primary:hover {
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
</style>
