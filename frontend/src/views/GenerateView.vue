<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import LuaPreview from '../components/LuaPreview.vue'
import { api, getApiErrorMessage, type ScriptTargetInfo } from '../api'
import { useProjectStore } from '../stores/project'

const router = useRouter()
const project = useProjectStore()
const targets = ref<ScriptTargetInfo[]>([])
const selectedTargetId = ref('logitech-ghub-lua')
const targetError = ref('')

onMounted(async () => {
  try {
    targets.value = await api.listScriptTargets()
    selectedTargetId.value = targets.value[0]?.id ?? selectedTargetId.value
  } catch (error) {
    targetError.value = getApiErrorMessage(error, '脚本目标加载失败')
  }
})

function handleRemoveGun(index: number) {
  project.removeGun(index)
  if (project.guns.length === 0) {
    router.push('/patterns/current/edit')
  }
}
</script>

<template>
  <section class="section generate-view">
    <div class="generate-toolbar">
      <button class="secondary-btn" @click="router.push('/patterns/current/edit')">返回编辑</button>
      <label>脚本目标</label>
      <select v-model="selectedTargetId">
        <option v-for="target in targets" :key="target.id" :value="target.id">
          {{ target.name }}
        </option>
      </select>
    </div>
    <div v-if="targetError" class="error">{{ targetError }}</div>

    <LuaPreview
      :guns="project.guns"
      :sensitivity="project.sensitivity"
      :target-id="selectedTargetId"
      :targets="targets"
      @remove="handleRemoveGun"
      @back="router.push('/patterns/current/edit')"
      @add-more="router.push('/import')"
    />
  </section>
</template>

<style scoped>
.generate-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.generate-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
}

.secondary-btn {
  padding: 8px 12px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #21262d;
  color: #c9d1d9;
  cursor: pointer;
}

.generate-toolbar label {
  color: #999;
  font-size: 0.9rem;
}

.generate-toolbar select {
  padding: 8px 10px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #0d1117;
  color: #c9d1d9;
}

.error {
  padding: 10px;
  border-radius: 6px;
  background: rgba(255, 123, 114, 0.12);
  color: #ff7b72;
}
</style>
