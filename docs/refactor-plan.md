# Recoil Studio Modernization Refactor Plan

## 目标

将 Recoil Studio 从当前的“前端单页步骤流 + FastAPI 服务脚本 + 生成 Lua 模板”的实现，重构为可扩展、可测试、可发布的现代化应用架构。核心方向是：现代路由、插件系统、Patch Manager、显式生命周期、类型化消息通道、模块测试、可复现构建。

本方案先定义技术路线和边界，不直接改业务代码。

## 当前状态

### 现有结构

```text
recoil-studio/
  backend/                 FastAPI 后端，同时托管前端构建产物
    main.py                应用入口、CORS、静态资源、API router 注册
    app/api/               pattern/lua 两组接口
    app/models/            Pydantic schema
    app/services/          OpenCV 识别、Lua 生成
    static/                前端构建产物，当前在仓库内
  frontend/                Vue 3 + Vite
    src/App.vue            单文件步骤状态机
    src/components/        上传、编辑器、Lua 预览等大组件
    src/api.ts             axios API client 与 DTO 类型
  data/                    Lua 预设数据
  pattern_generator.py     独立 CLI
  macro-G502.lua           示例/产物脚本
  build.bat/start.bat      Windows 批处理入口
```

### 主要问题

- `App.vue` 承担路由、流程状态、数据编排，页面无法深链、回退、分模块加载。
- `PatternEditor.vue` 超过千行，画布渲染、指针输入、历史记录、选择框、枪械配置、Lua 片段预览都耦合在一个组件中。
- 前端和后端 DTO 各自手写，缺少统一 contract，接口变更容易漂移。
- API 以功能文件直接注册，没有应用上下文、生命周期、依赖注入或插件机制。
- Lua 生成器是字符串模板单体，难以插入 patch、目标平台、按键映射、公式修正、脚本版本差异。
- 缺少 patch manager，无法对弹道、灵敏度公式、生成脚本做可追踪的变更集合。
- 缺少消息通道抽象，前端组件之间主要靠 props/emit，后端没有事件总线。
- 缺少模块测试和集成测试；识别算法、弹道计算、Lua 生成、编辑器状态机没有回归保护。
- `backend/static`、`__pycache__`、`node_modules` 这类产物/依赖目录出现在工作区，构建边界不清晰。
- 构建由 `.bat` 串联，缺少跨平台任务、锁定运行时、CI 可复现流程。

## 推荐技术路线

### 总体选择

推荐保留 Web 技术栈，但把应用升级为 TypeScript-first 的模块化架构：

- 前端：Vue 3 + Vue Router + Pinia + Vite/Vitest + Playwright。
- 后端：FastAPI + Pydantic v2 + pytest + httpx + uv/ruff/pyright。
- Contract：OpenAPI 作为后端真实契约，前端通过 `openapi-typescript` 生成类型。
- 构建任务：根目录统一用 `pnpm` 或 `npm` workspace 编排前端、API contract、测试脚本；Python 用 `uv` 管理虚拟环境和锁文件。
- 发布模式：开发期前后端分离；生产期后端只托管 `frontend/dist` 或由独立静态服务器托管，构建产物不入库。

### 不建议的方向

- 不建议全量迁移到 Electron/Tauri 作为第一阶段目标。当前需求仍是 Web 工具，先把架构边界、路由、插件、测试做好，桌面壳可以作为后续 adapter。
- 不建议把 OpenCV 识别迁到浏览器端。Python/OpenCV 目前是合理能力边界，前端只负责交互、可视化和局部状态。
- 不建议引入大型后端框架或数据库。现阶段核心是本地生成工具，持久化可先用 JSON workspace/project 文件。

## 目标架构

```text
recoil-studio/
  apps/
    web/                         Vue app
      src/
        app/                     app bootstrap, router, providers
        routes/                  route modules
        features/                feature slices
          import-pattern/
          pattern-editor/
          gun-library/
          script-generator/
          patch-manager/
        shared/                  UI, utils, message bus, API client
        plugins/                 frontend plugin registry
        tests/
    api/                         FastAPI app
      recoil_studio/
        app.py                   app factory
        routes/                  route modules
        core/                    config, lifecycle, errors, DI
        domain/                  pure domain models/services
        plugins/                 backend plugin registry
        patches/                 patch manager implementation
        adapters/                OpenCV, Lua target, storage
        tests/
  packages/
    contract/                    generated OpenAPI types/schema snapshots
    lua-runtime/                 Lua generation templates and target adapters
    test-fixtures/               sample images, recoil patterns, expected scripts
  docs/
  pyproject.toml
  package.json
```

## 路由设计

前端从 `currentStep` 改为真实路由。每个页面只负责页面级编排，业务能力由 feature module 提供。

```text
/                           dashboard 或最近项目
/import                     图片/数据导入
/patterns/:patternId/edit   弹道编辑器
/guns                       枪械配置库
/generate                   Lua/目标脚本生成
/patches                    Patch Manager
/settings                   全局设置、按键映射、灵敏度模板
```

路由模块示例边界：

- `routes/import.route.ts`：声明路由、懒加载页面、进入前加载插件能力。
- `features/import-pattern`：上传、数据解析、识别任务状态。
- `features/pattern-editor`：画布交互、选择、历史、弹道计算请求。
- `features/script-generator`：目标平台、模板参数、生成与下载。
- `features/patch-manager`：patch 列表、预览、应用/回滚、冲突检测。

## 插件系统

插件目标是把“识别算法、弹道转换、灵敏度公式、Lua 目标平台、UI 面板、patch 类型”变成可注册能力，而不是硬编码分支。

### 插件类型

- `PatternDetectorPlugin`：图片识别策略，例如绿色点识别、颜色阈值预设、未来 ML 检测。
- `PatternParserPlugin`：导入格式解析，例如 JSON、Lua table、CSV、纯文本。
- `TransformPlugin`：弹道缩放、平滑、反向、抽样、插值。
- `SensitivityFormulaPlugin`：FOV、MDV、ADS、屏息等公式策略。
- `ScriptTargetPlugin`：Lua G HUB、未来其他鼠标/驱动脚本目标。
- `EditorToolPlugin`：前端画布工具，例如框选、缩放、点吸附、批量移动。
- `PatchPlugin`：patch 类型定义、校验、预览、应用逻辑。

### 前端插件接口草案

```ts
export interface RecoilStudioPlugin {
  id: string
  version: string
  activate(ctx: PluginContext): void | Promise<void>
  deactivate?(ctx: PluginContext): void | Promise<void>
}

export interface PluginContext {
  routes: RouteRegistry
  panels: PanelRegistry
  commands: CommandRegistry
  messages: MessageBus
  patches: PatchRegistry
  lifecycle: LifecycleHooks
}
```

### 后端插件接口草案

```py
class BackendPlugin(Protocol):
    id: str
    version: str

    async def activate(self, ctx: PluginContext) -> None: ...
    async def deactivate(self, ctx: PluginContext) -> None: ...
```

后端 `PluginContext` 应暴露：router registry、service registry、event bus、patch registry、config、logger。

## Patch Manager

Patch Manager 是本次重构的核心，不只是 Git patch，而是业务层可审计变更集。

### Patch 对象

```ts
export interface StudioPatch {
  id: string
  title: string
  description?: string
  createdAt: string
  author?: string
  target: 'pattern' | 'gun' | 'sensitivity' | 'script-template' | 'project'
  operations: PatchOperation[]
  preconditions?: PatchPrecondition[]
  metadata?: Record<string, unknown>
}
```

### Operation 类型

- `set-field`：修改枪械、灵敏度、项目配置字段。
- `replace-pattern`：替换整条弹道。
- `transform-pattern`：应用缩放、平滑、裁剪、插值等算法。
- `insert-bullets` / `remove-bullets`：局部修改弹道。
- `replace-template-block`：替换 Lua 模板块。
- `formula-override`：替换灵敏度/FOV 公式。

### Patch 生命周期

```text
draft -> validated -> previewed -> applied -> committed
                         |            |
                         v            v
                      rejected      reverted
```

### Patch 能力要求

- 校验：检查目标存在、版本匹配、schema 合法、操作可应用。
- 预览：显示 before/after diff，包括弹道表格 diff、Lua diff、配置 diff。
- 应用：生成新的 project state，不直接原地突变。
- 回滚：保存 inverse patch 或基于 snapshot 回退。
- 冲突：同一字段/同一区间弹道被多个 patch 改动时标记冲突。
- 审计：记录 patch 来源、插件 id、应用时间、目标版本。

## 生命周期管理

### 应用生命周期

前端：

```text
createApp -> loadConfig -> installCorePlugins -> installUserPlugins -> createRouter -> hydrateProject -> mounted -> dispose
```

后端：

```text
create_app -> load_settings -> register_core_services -> register_plugins -> startup -> serving -> shutdown
```

### Feature 生命周期

每个 feature module 提供可选生命周期：

- `setup(ctx)`：注册命令、消息订阅、store。
- `beforeRouteEnter(route)`：加载项目或资源。
- `mounted()`：绑定 DOM/worker/流。
- `suspend()`：页面切走时暂停重任务。
- `dispose()`：释放事件监听、object URL、worker、timer。

### 长任务生命周期

图片识别、Lua 生成、patch 应用都按任务模型处理：

```text
queued -> running -> succeeded | failed | cancelled
```

每个任务必须有 task id、进度、取消信号、错误对象、日志片段。

## 消息通道

### 前端消息总线

使用类型化 event bus，避免跨组件层层 emit。

```ts
type AppEvents = {
  'pattern:detected': { patternId: string }
  'pattern:updated': { patternId: string; source: 'editor' | 'patch' }
  'patch:applied': { patchId: string }
  'script:generated': { target: string; bytes: number }
  'task:progress': { taskId: string; progress: number; message?: string }
}
```

适用范围：插件通信、命令执行结果、任务进度、跨 feature 通知。

不适用范围：局部组件输入值和纯 UI 状态，仍放在组件或 store 中。

### 前后端消息

第一阶段保持 HTTP API，长任务用轮询或 Server-Sent Events。只有在需要双向实时控制时才引入 WebSocket。

推荐接口：

```text
POST /api/tasks/pattern-detection
GET  /api/tasks/{taskId}
GET  /api/tasks/{taskId}/events      text/event-stream
POST /api/tasks/{taskId}/cancel
```

## 状态管理

前端分层：

- Route state：URL 参数、query、当前页面。
- Project state：当前项目、patterns、guns、patches、settings，使用 Pinia store。
- Task state：上传、识别、生成、patch 应用任务状态。
- Editor local state：画布 pan/zoom、hover、临时框选、拖拽中状态。

原则：可持久化的业务数据进入 project store；短暂交互状态留在 feature 内部。

## 后端模块化

将当前服务重组为纯 domain + adapter：

```text
domain/
  models.py                 Point, RecoilPattern, GunConfig, Sensitivity
  pattern_math.py           calculate_recoil_pattern 等纯函数
  script_model.py           目标脚本抽象
adapters/
  opencv_detector.py        OpenCV 识别实现
  lua_ghub_generator.py     Logitech G HUB Lua 生成实现
  project_storage.py        JSON 项目文件读写
routes/
  patterns.py
  scripts.py
  patches.py
  tasks.py
core/
  app_factory.py
  lifecycle.py
  errors.py
  settings.py
```

业务规则优先写成纯函数，API route 只负责请求解析、调用 use case、返回响应。

## 构建现代化

### 前端

- 使用 Vite 保留 Vue 3，但拆分为 `apps/web`。
- 加入 Vue Router、Pinia、Vitest、Testing Library、Playwright。
- 使用 `openapi-typescript` 从后端 OpenAPI 生成 DTO。
- 使用 `eslint` + `prettier` 或 `oxlint` + `prettier`，避免无格式规范。
- 构建产物输出 `apps/web/dist`，不写入后端源码目录。

### 后端

- 使用 `pyproject.toml` 管理依赖、ruff、pytest、pyright。
- 使用 `uv lock` 锁定 Python 依赖。
- FastAPI 应用使用 `create_app()` 工厂，测试可以创建独立 app。
- OpenCV 相关依赖作为可选 extra：`api[vision]`，便于无 GUI CI 安装 headless 版本。

### 根目录任务

```json
{
  "scripts": {
    "dev": "并行启动 api 与 web",
    "build": "构建 web、校验 api、生成 contract",
    "test": "运行前后端单元测试",
    "test:e2e": "运行 Playwright",
    "lint": "运行 TS 与 Python lint",
    "typecheck": "vue-tsc + pyright",
    "contract": "生成 OpenAPI types 并检查快照"
  }
}
```

## 测试策略

### Python 单元测试

重点覆盖：

- `calculate_recoil_pattern`：排序、delta 方向、缩放、空/单点输入。
- `opencv_detector`：用 fixture 图片测试绿色点识别数量和坐标容差。
- `lua_ghub_generator`：给定枪械和灵敏度，输出脚本 snapshot。
- `patch_manager`：validate、preview、apply、rollback、conflict。
- API routes：使用 `TestClient` 或 `httpx.AsyncClient` 测试请求/响应 schema。

### 前端单元测试

重点覆盖：

- parser plugins：JSON/Lua/CSV 输入解析。
- Pinia stores：project state、patch apply、task state。
- router guards：无 pattern 时进入编辑页的行为。
- message bus：订阅/取消订阅、类型事件分发。
- editor reducer/composable：选择、移动、缩放、撤销/重做。

### 前端组件测试

重点覆盖：

- import 页面上传成功/失败状态。
- patch preview diff 展示。
- script generator 参数修改触发重新生成。
- editor toolbar 状态，不测试 canvas 像素细节，复杂画布逻辑放到纯函数。

### E2E 测试

关键路径：

1. 导入 fixture 图片。
2. 识别弹道并进入编辑页。
3. 移动一个点并撤销/重做。
4. 添加枪械。
5. 应用一个 scaling patch。
6. 生成并下载 Lua。

## 迁移步骤

### Phase 0：清理与基线

- 添加 `.gitignore` 规则：`node_modules/`、`__pycache__/`、`backend/static/`、`dist/`、虚拟环境。
- 建立 `docs/refactor-plan.md`。
- 添加最小 smoke test：后端 health、Lua 生成、弹道计算。
- 固定当前行为快照，避免重构中丢能力。

### Phase 1：构建与测试底座

- 新增 `pyproject.toml`、pytest、ruff、pyright 配置。
- 前端加入 Vitest、Testing Library、基础 test setup。
- 后端改为 `create_app()` 工厂，但保持原接口兼容。
- 生成 OpenAPI contract，前端改用生成类型或先建立 contract 包。

### Phase 2：前端路由化

- 引入 Vue Router。
- 将 `currentStep` 拆为 `/import`、`/patterns/:id/edit`、`/generate`。
- 引入 Pinia project store，替代 App.vue 顶层状态散落。
- `App.vue` 降级为 layout + router-view。

### Phase 3：编辑器模块拆分

- 抽出 `useCanvasViewport`：pan/zoom/坐标转换。
- 抽出 `useSelection`：点选择、框选、hover。
- 抽出 `useHistory`：undo/redo。
- 抽出 `patternMath.ts`：纯弹道计算、缩放、diff。
- 保留 canvas 渲染组件，但移除枪械配置和 Lua 预览职责。

### Phase 4：插件系统与消息通道

- 实现前端 `PluginManager`、`MessageBus`、`CommandRegistry`。
- 将导入解析、编辑器工具、script target 先迁为内置插件。
- 后端实现 app lifecycle、service registry、backend plugin manager。
- 所有插件先作为 core plugins 随应用打包，不急于支持第三方动态加载。

### Phase 5：Patch Manager

- 定义 patch schema 与 operation schema。
- 实现 pattern/gun/sensitivity 三类 patch。
- 前端新增 `/patches` 路由和 patch preview UI。
- 后端提供 validate/preview/apply/revert API。
- 添加 patch conflict 与 rollback 测试。

### Phase 6：脚本生成现代化

- 把 Lua 模板拆成 header、config、runtime、event-handler、target adapter。
- 将 FOV/MDV/ADS 公式迁为 `SensitivityFormulaPlugin`。
- 为 Lua 生成建立 snapshot 测试。
- 生成结果附带 manifest：版本、插件、patch、输入 hash。

### Phase 7：发布与 CI

- 建立 GitHub Actions 或本地 CI 脚本：lint、typecheck、test、build。
- 移除仓库内构建产物和缓存目录。
- 提供跨平台启动脚本，Windows `.bat` 只作为薄封装。
- 文档更新：开发、测试、插件、patch 编写指南。

## 风险与控制

- 风险：一次性迁移目录导致大量路径变化，难以审查。控制：按 phase 小步提交，每步保持可运行。
- 风险：插件系统过度设计。控制：只实现当前内置插件需要的 registry，不做第三方远程加载。
- 风险：Patch Manager 与普通编辑重复。控制：编辑器直接改 project state，Patch Manager 用于批处理、导入修正、公式/模板变更和可审计操作。
- 风险：Canvas 交互回归难测。控制：把交互算法抽成纯函数，E2E 只覆盖主路径。
- 风险：FOV/MDV 公式本身存在业务不确定。控制：公式插件化，保留多个公式版本并用 fixture 对比。

## 第一轮可执行任务

1. 清理 `.gitignore` 并停止跟踪构建产物/缓存。
2. 添加后端 pytest，覆盖 `PatternDetector.calculate_recoil_pattern` 和 `LuaGenerator.generate`。
3. 添加前端 Vitest，覆盖导入数据 parser，先从 `ImageUpload.vue` 抽出 parser 函数。
4. 引入 Vue Router，把三步流程映射到路由，但保持 UI 行为不变。
5. 引入 Pinia project store，迁移 `points/pattern/guns/sensitivity/currentStep`。
6. 新建 `PluginManager` 和 `MessageBus`，先注册内置 parser/script target 插件。
7. 新建 Patch Manager 的 schema、纯函数实现和单元测试。

## 验收标准

- `npm run build`、`npm run test`、`pytest` 能在干净环境通过。
- 路由支持刷新和深链进入编辑/生成页面。
- 前端不再直接维护重复 DTO，类型来自 contract 或共享 schema。
- 新增一个导入格式、一个 Lua target 或一个 sensitivity formula 不需要修改核心页面组件。
- Patch 可以 validate、preview、apply、rollback，并有单元测试覆盖。
- Lua 输出对既有示例保持可比对快照，避免模板重构引入隐性行为变化。
