export type AppEvents = {
  'pattern:detected': { patternId: string }
  'pattern:updated': { patternId: string; source: 'editor' | 'patch' }
  'patch:applied': { patchId: string }
  'script:generated': { target: string; bytes: number }
  'task:progress': { taskId: string; progress: number; message?: string }
}
