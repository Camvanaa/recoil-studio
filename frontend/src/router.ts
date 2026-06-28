import { createRouter, createWebHistory } from 'vue-router'
import GenerateView from './views/GenerateView.vue'
import ImportView from './views/ImportView.vue'
import PatchesView from './views/PatchesView.vue'
import PatternEditView from './views/PatternEditView.vue'
import { useProjectStore } from './stores/project'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/import' },
    { path: '/import', component: ImportView },
    { path: '/patterns/current/edit', component: PatternEditView },
    { path: '/patches', component: PatchesView },
    { path: '/generate', component: GenerateView },
  ],
})

router.beforeEach((to) => {
  const project = useProjectStore()
  const hasPattern = project.pattern.length > 0
  const hasGuns = project.guns.length > 0

  if (to.path.startsWith('/patterns') && !hasPattern) {
    return '/import'
  }

  if (to.path.startsWith('/generate') && !hasGuns) {
    return hasPattern ? '/patterns/current/edit' : '/import'
  }

  return true
})
