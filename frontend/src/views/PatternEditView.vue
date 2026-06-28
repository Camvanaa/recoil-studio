<script setup lang="ts">
import { useRouter } from 'vue-router'
import PatternEditor from '../components/PatternEditor.vue'
import { useProjectStore } from '../stores/project'
import type { GunConfig } from '../api'

const router = useRouter()
const project = useProjectStore()

function handleAddGun(gun: GunConfig) {
  project.addGun(gun)
  router.push('/generate')
}

function handleBack() {
  project.resetPattern()
  router.push('/import')
}
</script>

<template>
  <section class="section pattern-edit-view">
    <div class="view-actions">
      <div class="summary">
        <span>{{ project.pattern.length }} 发弹道</span>
        <span>{{ project.guns.length }} 把枪械</span>
      </div>
      <button class="patch-btn" @click="router.push('/patches')">Patch Manager</button>
      <button class="patch-btn primary" :disabled="project.guns.length === 0" @click="router.push('/generate')">
        生成脚本
      </button>
    </div>
    <PatternEditor
      :points="project.points"
      :pattern="project.pattern"
      :image-url="project.imageUrl"
      :image-width="project.imageWidth"
      :image-height="project.imageHeight"
      @update="project.updatePattern"
      @add-gun="handleAddGun"
      @back="handleBack"
    />
  </section>
</template>

<style scoped>
.pattern-edit-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.view-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.summary {
  margin-right: auto;
  display: flex;
  gap: 10px;
  color: #999;
  font-size: 0.9rem;
}

.patch-btn {
  padding: 8px 14px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #21262d;
  color: #c9d1d9;
  cursor: pointer;
}

.patch-btn:hover {
  background: #30363d;
}

.patch-btn.primary {
  border-color: #667eea;
  background: #667eea;
  color: #fff;
}

.patch-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
