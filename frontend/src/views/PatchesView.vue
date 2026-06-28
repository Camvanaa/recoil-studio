<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, getApiErrorMessage, type PatchPreview, type StudioPatch } from '../api'
import { useRuntime } from '../app/runtimeContext'
import { patchTemplates, stringifyPatchTemplate, type PatchTemplate } from '../features/patches/templates'
import { useProjectStore } from '../stores/project'

const router = useRouter()
const runtime = useRuntime()
const project = useProjectStore()

const patchText = ref(JSON.stringify({
  id: 'scale-pattern',
  title: 'Scale current pattern',
  operations: [
    { type: 'transform-pattern', target: 'pattern', scale_y: 1.1, scale_x: 1 },
  ],
}, null, 2))
const preview = ref<PatchPreview | null>(null)
const error = ref('')
const success = ref('')
const isLoading = ref(false)

const canPatch = computed(() => project.pattern.length > 0 || project.guns.length > 0)

async function previewPatch() {
  error.value = ''
  success.value = ''
  preview.value = null
  isLoading.value = true

  try {
    const patch = parsePatch()
    preview.value = await api.previewPatch(project.getProjectState(), patch)
  } catch (err) {
    error.value = getApiErrorMessage(err, 'Patch preview failed')
  } finally {
    isLoading.value = false
  }
}

async function applyPatch() {
  error.value = ''
  success.value = ''
  isLoading.value = true

  try {
    const patch = parsePatch()
    const nextState = await api.applyPatch(project.getProjectState(), patch)
    project.applyProjectState(nextState)
    runtime.messages.emit('patch:applied', { patchId: patch.id })
    runtime.messages.emit('pattern:updated', { patternId: 'current', source: 'patch' })
    preview.value = null
    success.value = `已应用 ${patch.title || patch.id}`
  } catch (err) {
    error.value = getApiErrorMessage(err, 'Patch apply failed')
  } finally {
    isLoading.value = false
  }
}

function useTemplate(template: PatchTemplate) {
  patchText.value = stringifyPatchTemplate(template)
  preview.value = null
  error.value = ''
  success.value = ''
}

function parsePatch(): StudioPatch {
  const parsed: unknown = JSON.parse(patchText.value)
  if (!isPatch(parsed)) {
    throw new Error('Patch JSON must include id, title, and operations')
  }
  return parsed
}

function isPatch(value: unknown): value is StudioPatch {
  return typeof value === 'object'
    && value !== null
    && 'id' in value
    && 'title' in value
    && 'operations' in value
    && Array.isArray((value as { operations: unknown }).operations)
}
</script>

<template>
  <section class="section patches-view">
    <div class="patch-header">
      <div>
        <h2>Patch Manager</h2>
        <p>预览、验证并应用业务层 patch。</p>
      </div>
      <div class="patch-actions">
        <button class="btn btn-secondary" @click="router.push('/patterns/current/edit')">返回编辑</button>
        <button class="btn btn-secondary" @click="previewPatch" :disabled="isLoading || !canPatch">预览</button>
        <button class="btn btn-primary" @click="applyPatch" :disabled="isLoading || !canPatch">应用 Patch</button>
      </div>
    </div>

    <div v-if="!canPatch" class="notice">当前没有弹道或枪械数据，先导入数据再应用 patch。</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="success" class="success">{{ success }}</div>

    <div class="template-row">
      <span>模板</span>
      <button
        v-for="template in patchTemplates"
        :key="template.id"
        class="template-btn"
        @click="useTemplate(template)"
      >
        {{ template.label }}
      </button>
    </div>

    <div class="patch-grid">
      <textarea v-model="patchText" spellcheck="false" @input="success = ''; preview = null" />

      <div class="preview-panel">
        <h3>Preview</h3>
        <div v-if="isLoading" class="muted">处理中...</div>
        <div v-else-if="preview">
          <div :class="['status', preview.valid ? 'valid' : 'invalid']">
            {{ preview.valid ? 'Valid patch' : 'Invalid patch' }}
          </div>
          <ul v-if="preview.errors.length" class="errors">
            <li v-for="item in preview.errors" :key="item">{{ item }}</li>
          </ul>
          <div v-for="(change, index) in preview.changes" :key="index" class="change">
            <div class="change-title">{{ change.operation.type }} / {{ change.operation.target }}</div>
            <pre>{{ JSON.stringify({ before: change.before, after: change.after }, null, 2) }}</pre>
          </div>
        </div>
        <div v-else class="muted">点击预览查看变更。</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.patches-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.patch-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.patch-header h2 {
  margin-bottom: 6px;
  color: #a8e6cf;
}

.patch-header p,
.muted {
  color: #999;
}

.patch-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.patch-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

textarea,
.preview-panel {
  min-height: 420px;
  border: 1px solid #30363d;
  border-radius: 8px;
  background: #0d1117;
  color: #c9d1d9;
}

textarea {
  padding: 14px;
  font-family: Consolas, monospace;
  font-size: 0.9rem;
  resize: vertical;
}

.preview-panel {
  padding: 14px;
  overflow: auto;
}

.preview-panel h3 {
  margin-bottom: 12px;
}

.btn {
  padding: 9px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-secondary {
  background: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
}

.notice,
.error,
.success {
  padding: 10px;
  border-radius: 6px;
}

.notice {
  background: rgba(102, 126, 234, 0.15);
  color: #c9d1d9;
}

.error,
.errors {
  color: #ff7b72;
}

.success {
  background: rgba(168, 230, 207, 0.12);
  color: #a8e6cf;
}

.template-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  color: #999;
  font-size: 0.9rem;
}

.template-btn {
  padding: 7px 10px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #21262d;
  color: #c9d1d9;
  cursor: pointer;
}

.template-btn:hover {
  background: #30363d;
}

.status {
  margin-bottom: 12px;
  font-weight: 700;
}

.status.valid {
  color: #a8e6cf;
}

.status.invalid {
  color: #ff7b72;
}

.change {
  margin-top: 14px;
}

.change-title {
  margin-bottom: 6px;
  color: #8b949e;
}

pre {
  padding: 10px;
  border-radius: 6px;
  background: #161b22;
  overflow: auto;
  font-size: 0.8rem;
}

@media (max-width: 900px) {
  .patch-header,
  .patch-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
