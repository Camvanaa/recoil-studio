<script setup lang="ts">
import { useRouter } from 'vue-router'
import ImageUpload from '../components/ImageUpload.vue'
import type { Point, RecoilData } from '../api'
import { useProjectStore } from '../stores/project'

const router = useRouter()
const project = useProjectStore()

function handlePatternDetected(data: {
  points: Point[]
  pattern: RecoilData[]
  imageUrl: string
  width: number
  height: number
}) {
  project.setDetectedPattern(data)
  router.push('/patterns/current/edit')
}

function handleDataImported(data: { pattern: RecoilData[] }) {
  project.importPattern(data)
  router.push('/patterns/current/edit')
}
</script>

<template>
  <section class="section">
    <ImageUpload
      @detected="handlePatternDetected"
      @imported="handleDataImported"
    />
  </section>
</template>
