<script setup lang="ts">
import { ref, watch } from 'vue'
import { api, type GunConfig } from '../api'

const props = defineProps<{
  guns: GunConfig[]
}>()

const emit = defineEmits<{
  remove: [index: number]
  back: []
}>()

const luaCode = ref('')
const isLoading = ref(false)

watch(() => props.guns, async () => {
  if (props.guns.length === 0) {
    luaCode.value = ''
    return
  }
  
  isLoading.value = true
  try {
    const result = await api.generateLua(props.guns)
    if (result.success) {
      luaCode.value = result.lua_code
    }
  } catch (e) {
    console.error('生成失败', e)
  } finally {
    isLoading.value = false
  }
}, { immediate: true, deep: true })

function copyToClipboard() {
  navigator.clipboard.writeText(luaCode.value)
  alert('已复制到剪贴板')
}

async function downloadLua() {
  try {
    const blob = await api.downloadLua(props.guns)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'macro-G502.lua'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('下载失败', e)
  }
}
</script>

<template>
  <div class="lua-preview">
    <div class="sidebar">
      <h3>已添加的枪械</h3>
      
      <div class="guns-list">
        <div v-for="(gun, i) in guns" :key="i" class="gun-item">
          <div class="gun-info">
            <div class="gun-name">{{ gun.name }}</div>
            <div class="gun-stats">
              {{ gun.rpm }} RPM | {{ gun.pattern.length }} 发
            </div>
          </div>
          <button class="remove-btn" @click="emit('remove', i)">✕</button>
        </div>
      </div>
      
      <button class="btn btn-secondary" @click="emit('back')">
        ← 添加更多枪械
      </button>
    </div>
    
    <div class="code-section">
      <div class="code-header">
        <h3>生成的 Lua 代码</h3>
        <div class="code-actions">
          <button class="btn btn-small" @click="copyToClipboard">
            📋 复制
          </button>
          <button class="btn btn-small btn-primary" @click="downloadLua">
            ⬇️ 下载
          </button>
        </div>
      </div>
      
      <div v-if="isLoading" class="loading">
        正在生成...
      </div>
      
      <pre v-else class="code"><code>{{ luaCode }}</code></pre>
    </div>
  </div>
</template>

<style scoped>
.lua-preview {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  min-height: 500px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sidebar h3 {
  margin: 0;
  color: #667eea;
}

.guns-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.gun-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #1a1a2e;
  border-radius: 8px;
}

.gun-name {
  font-weight: bold;
}

.gun-stats {
  font-size: 0.85rem;
  color: #999;
  margin-top: 3px;
}

.remove-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: #f66;
  color: #fff;
  cursor: pointer;
  font-size: 0.9rem;
}

.remove-btn:hover {
  background: #e55;
}

.code-section {
  display: flex;
  flex-direction: column;
  background: #0a0a1a;
  border-radius: 8px;
  overflow: hidden;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #1a1a2e;
}

.code-header h3 {
  margin: 0;
}

.code-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-small {
  padding: 6px 12px;
  font-size: 0.85rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-secondary {
  background: #333;
  color: #fff;
}

.btn-secondary:hover {
  background: #444;
}

.loading {
  padding: 40px;
  text-align: center;
  color: #666;
}

.code {
  flex: 1;
  margin: 0;
  padding: 20px;
  overflow: auto;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  color: #a8e6cf;
  background: transparent;
}

@media (max-width: 900px) {
  .lua-preview {
    grid-template-columns: 1fr;
  }
}
</style>
