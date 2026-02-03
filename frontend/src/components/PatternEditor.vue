<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { api, type Point, type RecoilData } from '../api'

const props = defineProps<{
  points: Point[]
  pattern: RecoilData[]
  imageUrl: string
  imageWidth: number
  imageHeight: number
}>()

const emit = defineEmits<{
  update: [pattern: RecoilData[]]
  addGun: [gun: { name: string; rpm: number; vertical_mul: number; horizontal_mul: number; pattern: RecoilData[] }]
  back: []
}>()

// 画布相关
const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)

// 点数据
const localPoints = ref<Point[]>([])
const localPattern = ref<RecoilData[]>([])

// 视图控制
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const lastPanPos = ref({ x: 0, y: 0 })

// 点编辑 - 支持多选
const selectedIndices = ref<Set<number>>(new Set())
const isDraggingPoint = ref(false)
const hoveredIndex = ref<number | null>(null)
const dragStartPos = ref<{ x: number, y: number } | null>(null)

// 框选
const isBoxSelecting = ref(false)
const boxSelectStart = ref<{ x: number, y: number } | null>(null)
const boxSelectEnd = ref<{ x: number, y: number } | null>(null)

// 选中框缩放
type HandleType = 'nw' | 'n' | 'ne' | 'w' | 'e' | 'sw' | 's' | 'se' | null
const activeHandle = ref<HandleType>(null)
const isResizing = ref(false)
const resizeStartBounds = ref<{ minX: number, minY: number, maxX: number, maxY: number } | null>(null)
const resizeStartPoints = ref<Map<number, { x: number, y: number }>>(new Map())

// 撤销/重做
const history = ref<Point[][]>([])
const historyIndex = ref(-1)
const maxHistory = 50

// 枪械配置
const gunName = ref('AK-47')
const gunRpm = ref(600)
const verticalMul = ref(1.0)
const horizontalMul = ref(1.0)

// 输出缩放
const outputScaleX = ref(1.0)
const outputScaleY = ref(1.0)

// 背景图
const bgImage = ref<HTMLImageElement | null>(null)

// 计算画布尺寸
const canvasSize = computed(() => {
  const container = containerRef.value
  if (!container) return { width: 600, height: 500 }
  return {
    width: container.clientWidth,
    height: Math.max(400, container.clientHeight)
  }
})

// 是否可以撤销/重做
const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

// 生成 Lua pattern 代码
const luaPatternCode = computed(() => {
  if (localPattern.value.length === 0) return 'pattern = {\n}'
  
  const lines = localPattern.value.map((p, i) => {
    // 格式: {y=值, x=值}, -- 第N发
    const y = Math.round(p.y * 1000000) / 1000000  // 保留精度但去掉多余小数
    const x = Math.round(p.x * 1000000) / 1000000
    return `    {y=${y}, x=${x}},    -- 第${i + 1}发`
  })
  
  return `pattern = {\n${lines.join('\n')}\n}`
})

// 计算选中点的边界框（世界坐标）
const selectionBounds = computed(() => {
  if (selectedIndices.value.size < 2) return null
  
  let minX = Infinity, maxX = -Infinity
  let minY = Infinity, maxY = -Infinity
  
  for (const idx of selectedIndices.value) {
    const p = localPoints.value[idx]
    if (p) {
      minX = Math.min(minX, p.x)
      maxX = Math.max(maxX, p.x)
      minY = Math.min(minY, p.y)
      maxY = Math.max(maxY, p.y)
    }
  }
  
  // 至少需要有一定的宽高才显示边界框
  const width = maxX - minX
  const height = maxY - minY
  if (width < 1 && height < 1) return null
  
  return { minX, minY, maxX, maxY, width, height }
})

// 获取八个控制点的位置（屏幕坐标）
function getHandlePositions(bounds: { minX: number, minY: number, maxX: number, maxY: number }) {
  const tl = worldToScreen(bounds.minX, bounds.minY)
  const tr = worldToScreen(bounds.maxX, bounds.minY)
  const bl = worldToScreen(bounds.minX, bounds.maxY)
  const br = worldToScreen(bounds.maxX, bounds.maxY)
  
  return {
    nw: tl,
    n: { x: (tl.x + tr.x) / 2, y: tl.y },
    ne: tr,
    w: { x: tl.x, y: (tl.y + bl.y) / 2 },
    e: { x: tr.x, y: (tr.y + br.y) / 2 },
    sw: bl,
    s: { x: (bl.x + br.x) / 2, y: bl.y },
    se: br
  }
}

// 检测鼠标是否在控制点上
function findHandleAt(screenX: number, screenY: number): HandleType {
  if (!selectionBounds.value) return null
  
  const handles = getHandlePositions(selectionBounds.value)
  const threshold = 8
  
  for (const [key, pos] of Object.entries(handles)) {
    const dist = Math.sqrt((pos.x - screenX) ** 2 + (pos.y - screenY) ** 2)
    if (dist < threshold) {
      return key as HandleType
    }
  }
  return null
}

// 初始化
watch(() => props.points, (newPoints) => {
  localPoints.value = newPoints.map(p => ({ ...p }))
  localPattern.value = [...props.pattern]
  // 初始化历史记录
  history.value = [newPoints.map(p => ({ ...p }))]
  historyIndex.value = 0
  centerView()
}, { immediate: true })

watch(() => props.pattern, (newPattern) => {
  localPattern.value = [...newPattern]
}, { deep: true })

onMounted(() => {
  if (props.imageUrl) {
    const img = new Image()
    img.onload = () => {
      bgImage.value = img
      draw()
    }
    img.src = props.imageUrl
  }
  
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeyDown)
  centerView()
  draw()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeyDown)
})

function handleResize() {
  draw()
}

// 保存历史记录
function saveHistory() {
  // 删除当前位置之后的历史
  history.value = history.value.slice(0, historyIndex.value + 1)
  // 添加当前状态
  history.value.push(localPoints.value.map(p => ({ ...p })))
  // 限制历史长度
  if (history.value.length > maxHistory) {
    history.value.shift()
  } else {
    historyIndex.value++
  }
}

// 撤销
function undo() {
  if (!canUndo.value) return
  historyIndex.value--
  const historyState = history.value[historyIndex.value]
  if (historyState) {
    localPoints.value = historyState.map(p => ({ ...p }))
    recalculatePattern()
    draw()
  }
}

// 重做
function redo() {
  if (!canRedo.value) return
  historyIndex.value++
  const historyState = history.value[historyIndex.value]
  if (historyState) {
    localPoints.value = historyState.map(p => ({ ...p }))
    recalculatePattern()
    draw()
  }
}

// 键盘事件
function handleKeyDown(e: KeyboardEvent) {
  // Ctrl+Z 撤销
  if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
    e.preventDefault()
    undo()
    return
  }
  
  // Ctrl+Shift+Z 或 Ctrl+Y 重做
  if ((e.ctrlKey && e.shiftKey && e.key === 'z') || (e.ctrlKey && e.key === 'y')) {
    e.preventDefault()
    redo()
    return
  }
  
  // Ctrl+A 全选
  if (e.ctrlKey && e.key === 'a') {
    e.preventDefault()
    selectAll()
    return
  }
  
  // Escape 取消选择
  if (e.key === 'Escape') {
    selectedIndices.value.clear()
    draw()
    return
  }
  
  // 方向键微调
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    if (selectedIndices.value.size === 0) return
    e.preventDefault()
    
    const step = e.shiftKey ? 10 : 1  // Shift加速
    let dx = 0, dy = 0
    
    switch (e.key) {
      case 'ArrowUp': dy = -step; break
      case 'ArrowDown': dy = step; break
      case 'ArrowLeft': dx = -step; break
      case 'ArrowRight': dx = step; break
    }
    
    // 移动选中的点
    for (const idx of selectedIndices.value) {
      const p = localPoints.value[idx]
      if (p) {
        p.x += dx / zoom.value
        p.y += dy / zoom.value
      }
    }
    
    draw()
    return
  }
}

// 键盘抬起时保存历史
function handleKeyUp(e: KeyboardEvent) {
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    if (selectedIndices.value.size > 0) {
      saveHistory()
      recalculatePattern()
    }
  }
}

// 全选
function selectAll() {
  selectedIndices.value = new Set(localPoints.value.map((_, i) => i))
  draw()
}

function centerView() {
  if (localPoints.value.length === 0) return
  
  let minX = Infinity, maxX = -Infinity
  let minY = Infinity, maxY = -Infinity
  
  for (const p of localPoints.value) {
    minX = Math.min(minX, p.x)
    maxX = Math.max(maxX, p.x)
    minY = Math.min(minY, p.y)
    maxY = Math.max(maxY, p.y)
  }
  
  const width = maxX - minX || 100
  const height = maxY - minY || 100
  const centerX = (minX + maxX) / 2
  const centerY = (minY + maxY) / 2
  
  const padding = 60
  const availWidth = canvasSize.value.width - padding * 2
  const availHeight = canvasSize.value.height - padding * 2
  
  zoom.value = Math.min(availWidth / width, availHeight / height, 3)
  panX.value = canvasSize.value.width / 2 - centerX * zoom.value
  panY.value = canvasSize.value.height / 2 - centerY * zoom.value
  
  draw()
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  canvas.width = canvasSize.value.width
  canvas.height = canvasSize.value.height
  
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 绘制背景
  ctx.fillStyle = '#0d1117'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // 绘制网格
  drawGrid(ctx)
  
  // 绘制背景图
  if (bgImage.value && props.imageUrl) {
    ctx.save()
    ctx.globalAlpha = 0.3
    ctx.translate(panX.value, panY.value)
    ctx.scale(zoom.value, zoom.value)
    ctx.drawImage(bgImage.value, 0, 0)
    ctx.restore()
  }
  
  // 绘制弹道
  drawPattern(ctx)
  
  // 绘制选中框和控制点
  drawSelectionBox(ctx)
  
  // 绘制框选区域
  if (isBoxSelecting.value && boxSelectStart.value && boxSelectEnd.value) {
    ctx.strokeStyle = 'rgba(102, 126, 234, 0.8)'
    ctx.fillStyle = 'rgba(102, 126, 234, 0.1)'
    ctx.lineWidth = 1
    ctx.setLineDash([5, 5])
    
    const x = Math.min(boxSelectStart.value.x, boxSelectEnd.value.x)
    const y = Math.min(boxSelectStart.value.y, boxSelectEnd.value.y)
    const w = Math.abs(boxSelectEnd.value.x - boxSelectStart.value.x)
    const h = Math.abs(boxSelectEnd.value.y - boxSelectStart.value.y)
    
    ctx.fillRect(x, y, w, h)
    ctx.strokeRect(x, y, w, h)
    ctx.setLineDash([])
  }
}

function drawGrid(ctx: CanvasRenderingContext2D) {
  const gridSize = 50 * zoom.value
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)'
  ctx.lineWidth = 1
  
  const startX = panX.value % gridSize
  for (let x = startX; x < canvasSize.value.width; x += gridSize) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, canvasSize.value.height)
    ctx.stroke()
  }
  
  const startY = panY.value % gridSize
  for (let y = startY; y < canvasSize.value.height; y += gridSize) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(canvasSize.value.width, y)
    ctx.stroke()
  }
}

function drawPattern(ctx: CanvasRenderingContext2D) {
  if (localPoints.value.length === 0) return
  
  ctx.save()
  ctx.translate(panX.value, panY.value)
  ctx.scale(zoom.value, zoom.value)
  
  // 绘制连线
  ctx.strokeStyle = 'rgba(102, 126, 234, 0.6)'
  ctx.lineWidth = 2 / zoom.value
  ctx.beginPath()
  localPoints.value.forEach((point, i) => {
    if (i === 0) {
      ctx.moveTo(point.x, point.y)
    } else {
      ctx.lineTo(point.x, point.y)
    }
  })
  ctx.stroke()
  
  // 绘制点
  localPoints.value.forEach((point, i) => {
    const isSelected = selectedIndices.value.has(i)
    const isHovered = hoveredIndex.value === i
    const radius = (isSelected ? 8 : isHovered ? 7 : 6) / zoom.value
    
    // 选中高亮圈
    if (isSelected) {
      ctx.beginPath()
      ctx.arc(point.x, point.y, radius + 3 / zoom.value, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(255, 107, 107, 0.5)'
      ctx.lineWidth = 2 / zoom.value
      ctx.stroke()
    }
    
    // 外圈
    ctx.beginPath()
    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2)
    ctx.fillStyle = isSelected ? '#ff6b6b' : isHovered ? '#a8e6cf' : '#667eea'
    ctx.fill()
    
    // 内圈
    ctx.beginPath()
    ctx.arc(point.x, point.y, radius * 0.5, 0, Math.PI * 2)
    ctx.fillStyle = '#fff'
    ctx.fill()
    
    // 序号
    if (zoom.value > 0.5) {
      ctx.fillStyle = '#fff'
      ctx.font = `${12 / zoom.value}px sans-serif`
      ctx.textAlign = 'left'
      ctx.fillText(`${i + 1}`, point.x + radius + 4 / zoom.value, point.y + 4 / zoom.value)
    }
  })
  
  ctx.restore()
}

// 绘制选中框和八向控制点
function drawSelectionBox(ctx: CanvasRenderingContext2D) {
  const bounds = selectionBounds.value
  if (!bounds) return
  
  const handles = getHandlePositions(bounds)
  
  // 绘制边界框
  ctx.strokeStyle = 'rgba(88, 166, 255, 0.8)'
  ctx.lineWidth = 1
  ctx.setLineDash([4, 4])
  
  const tl = worldToScreen(bounds.minX, bounds.minY)
  const br = worldToScreen(bounds.maxX, bounds.maxY)
  const width = br.x - tl.x
  const height = br.y - tl.y
  
  ctx.strokeRect(tl.x, tl.y, width, height)
  ctx.setLineDash([])
  
  // 绘制八个控制点
  const handleSize = 8
  const handleStyle = {
    fill: '#fff',
    stroke: '#58a6ff',
    lineWidth: 2
  }
  
  ctx.fillStyle = handleStyle.fill
  ctx.strokeStyle = handleStyle.stroke
  ctx.lineWidth = handleStyle.lineWidth
  
  for (const [, pos] of Object.entries(handles)) {
    ctx.beginPath()
    ctx.rect(pos.x - handleSize / 2, pos.y - handleSize / 2, handleSize, handleSize)
    ctx.fill()
    ctx.stroke()
  }
}

// 坐标转换
function screenToWorld(x: number, y: number): { x: number, y: number } {
  return {
    x: (x - panX.value) / zoom.value,
    y: (y - panY.value) / zoom.value
  }
}

function worldToScreen(x: number, y: number): { x: number, y: number } {
  return {
    x: x * zoom.value + panX.value,
    y: y * zoom.value + panY.value
  }
}

function getMousePos(e: MouseEvent): { x: number, y: number } {
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
}

function findPointAt(worldX: number, worldY: number): number | null {
  const threshold = 15 / zoom.value
  for (let i = 0; i < localPoints.value.length; i++) {
    const p = localPoints.value[i]
    if (!p) continue
    const dist = Math.sqrt((p.x - worldX) ** 2 + (p.y - worldY) ** 2)
    if (dist < threshold) {
      return i
    }
  }
  return null
}

// 鼠标事件
function handleMouseDown(e: MouseEvent) {
  const pos = getMousePos(e)
  const world = screenToWorld(pos.x, pos.y)
  
  // 右键或中键平移
  if (e.button === 2 || e.button === 1) {
    isPanning.value = true
    lastPanPos.value = pos
    e.preventDefault()
    return
  }
  
  // 检测是否点击了控制点
  const handle = findHandleAt(pos.x, pos.y)
  if (handle && selectionBounds.value) {
    isResizing.value = true
    activeHandle.value = handle
    resizeStartBounds.value = { ...selectionBounds.value }
    // 保存所有选中点的原始位置
    resizeStartPoints.value = new Map()
    for (const idx of selectedIndices.value) {
      const p = localPoints.value[idx]
      if (p) {
        resizeStartPoints.value.set(idx, { x: p.x, y: p.y })
      }
    }
    dragStartPos.value = world
    return
  }
  
  const index = findPointAt(world.x, world.y)
  
  // Shift+左键：开始框选
  if (e.button === 0 && e.shiftKey && index === null) {
    isBoxSelecting.value = true
    boxSelectStart.value = pos
    boxSelectEnd.value = pos
    return
  }
  
  // Alt+左键：平移
  if (e.button === 0 && e.altKey) {
    isPanning.value = true
    lastPanPos.value = pos
    e.preventDefault()
    return
  }
  
  if (e.button === 0) {
    if (index !== null) {
      // 点击点
      if (e.ctrlKey) {
        // Ctrl+点击：切换选择
        if (selectedIndices.value.has(index)) {
          selectedIndices.value.delete(index)
        } else {
          selectedIndices.value.add(index)
        }
      } else if (!selectedIndices.value.has(index)) {
        // 点击未选中的点：单选
        selectedIndices.value.clear()
        selectedIndices.value.add(index)
      }
      // 开始拖动
      isDraggingPoint.value = true
      dragStartPos.value = world
    } else {
      // 点击空白处
      if (!e.ctrlKey) {
        selectedIndices.value.clear()
      }
      // 开始框选
      isBoxSelecting.value = true
      boxSelectStart.value = pos
      boxSelectEnd.value = pos
    }
    draw()
  }
}

function handleMouseMove(e: MouseEvent) {
  const pos = getMousePos(e)
  
  // 平移
  if (isPanning.value) {
    panX.value += pos.x - lastPanPos.value.x
    panY.value += pos.y - lastPanPos.value.y
    lastPanPos.value = pos
    draw()
    return
  }
  
  // 缩放选中框
  if (isResizing.value && activeHandle.value && resizeStartBounds.value && dragStartPos.value) {
    const world = screenToWorld(pos.x, pos.y)
    applyResize(world)
    draw()
    return
  }
  
  // 框选
  if (isBoxSelecting.value) {
    boxSelectEnd.value = pos
    draw()
    return
  }
  
  // 拖动点
  if (isDraggingPoint.value && selectedIndices.value.size > 0 && dragStartPos.value) {
    const world = screenToWorld(pos.x, pos.y)
    const dx = world.x - dragStartPos.value.x
    const dy = world.y - dragStartPos.value.y
    
    // 移动所有选中的点
    for (const idx of selectedIndices.value) {
      const p = localPoints.value[idx]
      const historyState = history.value[historyIndex.value]
      if (p && historyState) {
        // 从原始位置计算（避免累积误差）
        const original = historyState[idx]
        if (original) {
          p.x = original.x + dx
          p.y = original.y + dy
        }
      }
    }
    draw()
    return
  }
  
  // 检测控制点悬停，更新光标
  const handle = findHandleAt(pos.x, pos.y)
  updateCursor(handle)
  
  // 悬停检测
  const world = screenToWorld(pos.x, pos.y)
  const index = findPointAt(world.x, world.y)
  if (hoveredIndex.value !== index) {
    hoveredIndex.value = index
    draw()
  }
}

// 应用缩放变换
function applyResize(currentWorld: { x: number, y: number }) {
  if (!resizeStartBounds.value || !dragStartPos.value || !activeHandle.value) return
  
  const startBounds = resizeStartBounds.value
  const handle = activeHandle.value
  
  // 计算新的边界
  let newMinX = startBounds.minX
  let newMinY = startBounds.minY
  let newMaxX = startBounds.maxX
  let newMaxY = startBounds.maxY
  
  const dx = currentWorld.x - dragStartPos.value.x
  const dy = currentWorld.y - dragStartPos.value.y
  
  // 根据控制点类型调整边界
  if (handle.includes('w')) newMinX = startBounds.minX + dx
  if (handle.includes('e')) newMaxX = startBounds.maxX + dx
  if (handle.includes('n')) newMinY = startBounds.minY + dy
  if (handle.includes('s')) newMaxY = startBounds.maxY + dy
  
  // 计算缩放比例
  const oldWidth = startBounds.maxX - startBounds.minX
  const oldHeight = startBounds.maxY - startBounds.minY
  const newWidth = newMaxX - newMinX
  const newHeight = newMaxY - newMinY
  
  // 防止翻转（宽高不能为负）
  if (newWidth <= 0 || newHeight <= 0) return
  
  const scaleX = oldWidth > 0 ? newWidth / oldWidth : 1
  const scaleY = oldHeight > 0 ? newHeight / oldHeight : 1
  
  // 确定缩放基准点
  let pivotX = startBounds.minX
  let pivotY = startBounds.minY
  
  if (handle.includes('w')) pivotX = startBounds.maxX
  if (handle.includes('e')) pivotX = startBounds.minX
  if (handle.includes('n')) pivotY = startBounds.maxY
  if (handle.includes('s')) pivotY = startBounds.minY
  
  // 应用缩放到所有选中的点
  for (const [idx, original] of resizeStartPoints.value) {
    const p = localPoints.value[idx]
    if (p) {
      // 只在对应方向上缩放
      if (handle === 'n' || handle === 's') {
        // 只垂直缩放
        p.x = original.x
        p.y = pivotY + (original.y - pivotY) * scaleY
      } else if (handle === 'w' || handle === 'e') {
        // 只水平缩放
        p.x = pivotX + (original.x - pivotX) * scaleX
        p.y = original.y
      } else {
        // 角落控制点：双向缩放
        p.x = pivotX + (original.x - pivotX) * scaleX
        p.y = pivotY + (original.y - pivotY) * scaleY
      }
    }
  }
}

// 更新光标样式
function updateCursor(handle: HandleType) {
  const canvas = canvasRef.value
  if (!canvas) return
  
  if (!handle) {
    canvas.style.cursor = 'crosshair'
    return
  }
  
  const cursorMap: Record<string, string> = {
    nw: 'nwse-resize',
    se: 'nwse-resize',
    ne: 'nesw-resize',
    sw: 'nesw-resize',
    n: 'ns-resize',
    s: 'ns-resize',
    w: 'ew-resize',
    e: 'ew-resize'
  }
  
  canvas.style.cursor = cursorMap[handle] || 'crosshair'
}

function handleMouseUp(e: MouseEvent) {
  // 结束缩放
  if (isResizing.value) {
    isResizing.value = false
    activeHandle.value = null
    resizeStartBounds.value = null
    resizeStartPoints.value.clear()
    dragStartPos.value = null
    saveHistory()
    recalculatePattern()
    draw()
  }
  
  // 结束框选
  if (isBoxSelecting.value && boxSelectStart.value && boxSelectEnd.value) {
    // 计算框选范围内的点
    const x1 = Math.min(boxSelectStart.value.x, boxSelectEnd.value.x)
    const y1 = Math.min(boxSelectStart.value.y, boxSelectEnd.value.y)
    const x2 = Math.max(boxSelectStart.value.x, boxSelectEnd.value.x)
    const y2 = Math.max(boxSelectStart.value.y, boxSelectEnd.value.y)
    
    // 只有框选区域足够大时才选择
    if (Math.abs(x2 - x1) > 5 || Math.abs(y2 - y1) > 5) {
      if (!e.ctrlKey) {
        selectedIndices.value.clear()
      }
      
      localPoints.value.forEach((p, i) => {
        const screen = worldToScreen(p.x, p.y)
        if (screen.x >= x1 && screen.x <= x2 && screen.y >= y1 && screen.y <= y2) {
          selectedIndices.value.add(i)
        }
      })
    }
    
    isBoxSelecting.value = false
    boxSelectStart.value = null
    boxSelectEnd.value = null
    draw()
  }
  
  // 结束拖动点
  if (isDraggingPoint.value) {
    isDraggingPoint.value = false
    dragStartPos.value = null
    saveHistory()
    recalculatePattern()
  }
  
  isPanning.value = false
}

function handleWheel(e: WheelEvent) {
  e.preventDefault()
  
  const pos = getMousePos(e)
  const worldBefore = screenToWorld(pos.x, pos.y)
  
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  zoom.value = Math.max(0.1, Math.min(10, zoom.value * delta))
  
  const worldAfter = screenToWorld(pos.x, pos.y)
  panX.value += (worldAfter.x - worldBefore.x) * zoom.value
  panY.value += (worldAfter.y - worldBefore.y) * zoom.value
  
  draw()
}

// 重新计算弹道数据
async function recalculatePattern() {
  try {
    const result = await api.recalculatePattern(
      localPoints.value,
      outputScaleX.value,
      outputScaleY.value
    )
    if (result.success) {
      localPattern.value = result.pattern
      emit('update', result.pattern)
    }
  } catch (e) {
    console.error('重新计算失败', e)
  }
}

// 添加枪械
function handleAddGun() {
  if (!gunName.value.trim()) {
    alert('请输入枪械名称')
    return
  }
  
  emit('addGun', {
    name: gunName.value.trim(),
    rpm: gunRpm.value,
    vertical_mul: verticalMul.value,
    horizontal_mul: horizontalMul.value,
    pattern: localPattern.value
  })
}

// 工具函数
function zoomIn() {
  zoom.value = Math.min(10, zoom.value * 1.2)
  draw()
}

function zoomOut() {
  zoom.value = Math.max(0.1, zoom.value / 1.2)
  draw()
}

function resetView() {
  centerView()
}

watch([outputScaleX, outputScaleY], () => {
  recalculatePattern()
})

// 复制 Lua 代码
function copyLuaCode() {
  navigator.clipboard.writeText(luaPatternCode.value).then(() => {
    alert('已复制到剪贴板')
  }).catch(() => {
    // fallback
    const textarea = document.createElement('textarea')
    textarea.value = luaPatternCode.value
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    alert('已复制到剪贴板')
  })
}
</script>

<template>
  <div class="pattern-editor" @keyup="handleKeyUp" tabindex="0">
    <div class="editor-layout">
      <!-- 左侧：画布 -->
      <div class="canvas-section">
        <div class="toolbar">
          <div class="tool-group">
            <button class="tool-btn" @click="undo" :disabled="!canUndo" title="撤销 (Ctrl+Z)">↶</button>
            <button class="tool-btn" @click="redo" :disabled="!canRedo" title="重做 (Ctrl+Y)">↷</button>
            <div class="divider"></div>
            <button class="tool-btn" @click="zoomOut" title="缩小">−</button>
            <span class="zoom-level">{{ Math.round(zoom * 100) }}%</span>
            <button class="tool-btn" @click="zoomIn" title="放大">+</button>
            <button class="tool-btn" @click="resetView" title="重置视图">⌂</button>
          </div>
          <div class="tool-info">
            <span v-if="selectedIndices.size > 0">
              选中 {{ selectedIndices.size }} 个点 | 方向键微调
            </span>
            <span v-else>
              框选多选 | Ctrl+点击 | 滚轮缩放
            </span>
          </div>
        </div>
        
        <div class="canvas-container" ref="containerRef">
          <canvas
            ref="canvasRef"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @mouseleave="handleMouseUp"
            @wheel="handleWheel"
            @contextmenu.prevent
          />
        </div>
        
        <div class="shortcuts-hint">
          <span>右键拖动画布</span>
          <span>Ctrl+Z 撤销</span>
          <span>Ctrl+Y 重做</span>
          <span>Ctrl+A 全选</span>
          <span>方向键微调</span>
          <span>Shift加速</span>
        </div>
      </div>
      
      <!-- 右侧：配置面板 -->
      <div class="config-panel">
        <div class="panel-section">
          <h3>输出缩放</h3>
          <div class="scale-inputs">
            <div class="input-group">
              <label>X轴</label>
              <input type="number" v-model.number="outputScaleX" step="0.1" min="0.1" />
            </div>
            <div class="input-group">
              <label>Y轴</label>
              <input type="number" v-model.number="outputScaleY" step="0.1" min="0.1" />
            </div>
          </div>
        </div>
        
        <div class="panel-section">
          <h3>枪械配置</h3>
          <div class="input-group">
            <label>名称</label>
            <input type="text" v-model="gunName" placeholder="AK-47" />
          </div>
          <div class="input-group">
            <label>射速 (RPM)</label>
            <input type="number" v-model.number="gunRpm" min="100" max="1500" />
          </div>
          <div class="input-row">
            <div class="input-group">
              <label>垂直倍率</label>
              <input type="number" v-model.number="verticalMul" step="0.1" min="0.1" />
            </div>
            <div class="input-group">
              <label>水平倍率</label>
              <input type="number" v-model.number="horizontalMul" step="0.1" min="0.1" />
            </div>
          </div>
        </div>
        
        <div class="panel-section lua-section">
          <div class="lua-header">
            <h3>Lua Pattern ({{ localPattern.length }} 发)</h3>
            <button class="copy-btn" @click="copyLuaCode" title="复制代码">复制</button>
          </div>
          <div class="lua-code-wrapper">
            <pre class="lua-code"><code>{{ luaPatternCode }}</code></pre>
          </div>
        </div>
        
        <div class="panel-actions">
          <button class="btn btn-secondary" @click="emit('back')">← 返回</button>
          <button class="btn btn-primary" @click="handleAddGun">添加枪械 →</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pattern-editor {
  height: 100%;
  outline: none;
}

.editor-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 20px;
  height: 100%;
}

/* 画布区域 */
.canvas-section {
  display: flex;
  flex-direction: column;
  background: #0d1117;
  border-radius: 8px;
  overflow: hidden;
  min-height: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  flex-shrink: 0;
}

.tool-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.divider {
  width: 1px;
  height: 20px;
  background: #30363d;
  margin: 0 8px;
}

.tool-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #21262d;
  color: #c9d1d9;
  cursor: pointer;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.tool-btn:hover:not(:disabled) {
  background: #30363d;
  border-color: #8b949e;
}

.tool-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.zoom-level {
  min-width: 50px;
  text-align: center;
  font-size: 0.85rem;
  color: #8b949e;
}

.tool-info {
  font-size: 0.85rem;
  color: #8b949e;
}

.canvas-container {
  flex: 1;
  min-height: 300px;
}

canvas {
  width: 100%;
  height: 100%;
  cursor: crosshair;
}

.shortcuts-hint {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 15px;
  background: #161b22;
  border-top: 1px solid #30363d;
  font-size: 0.75rem;
  color: #6e7681;
  flex-shrink: 0;
}

.shortcuts-hint span {
  white-space: nowrap;
}

/* 配置面板 */
.config-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  min-height: 0;
}

.panel-section {
  background: #161b22;
  border-radius: 8px;
  padding: 12px 15px;
  flex-shrink: 0;
}

.panel-section h3 {
  font-size: 0.8rem;
  color: #8b949e;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.lua-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.lua-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.lua-header h3 {
  margin-bottom: 0;
}

.copy-btn {
  padding: 4px 10px;
  font-size: 0.75rem;
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 4px;
  color: #8b949e;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: #30363d;
  color: #c9d1d9;
}

.lua-code-wrapper {
  flex: 1;
  overflow: auto;
  background: #0d1117;
  border-radius: 6px;
  min-height: 0;
}

.lua-code {
  margin: 0;
  padding: 10px 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  color: #c9d1d9;
  white-space: pre;
  overflow-x: auto;
}

.lua-code code {
  font-family: inherit;
}

.scale-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-group label {
  font-size: 0.75rem;
  color: #8b949e;
}

.input-group input {
  padding: 6px 10px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #0d1117;
  color: #c9d1d9;
  font-size: 0.85rem;
}

.input-group input:focus {
  outline: none;
  border-color: #58a6ff;
}

.input-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

/* 按钮 */
.panel-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.btn {
  flex: 1;
  padding: 10px 15px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
}

.btn-secondary:hover {
  background: #30363d;
}

@media (max-width: 900px) {
  .editor-layout {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr auto;
  }
  
  .config-panel {
    max-height: 300px;
  }
  
  .lua-section {
    max-height: 150px;
  }
}
</style>
