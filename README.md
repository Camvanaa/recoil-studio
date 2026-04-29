# Recoil Studio

FPS 游戏压枪弹道可视化编辑器 + 罗技鼠标宏脚本

从弹道图片自动提取控制点，可视化编辑调整，一键生成 Logitech G HUB 可用的 Lua 脚本。

![Recoil Studio](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vue.js) ![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python) ![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey)

说在前面!!!! 最新版本的fov和mdv公式有问题 导致切换倍镜可能不准 有思路的欢迎pr

## 功能特性

- **图像识别** - 自动从弹道图片提取绿色标记点
- **可视化编辑** - 拖动、多选、框选、八向缩放
- **实时预览** - Lua 代码同步生成
- **多枪械支持** - 配置多把枪，游戏中一键切换
- **亚像素精度** - 误差累加算法，精确到子像素

## 项目结构

```
recoil-studio/
├── start.bat               # 一键启动
├── macro-G502.lua          # Lua 宏脚本（导入 G HUB）
├── pattern_generator.py    # CLI 弹道生成器
├── data/                   # 预设弹道数据
│   ├── m14.lua
│   └── ash-12.lua
├── backend/                # FastAPI 后端
│   ├── main.py
│   ├── requirements.txt
│   └── app/
└── frontend/               # Vue 3 前端
    ├── package.json
    └── src/
```

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourname/recoil-studio.git
cd recoil-studio

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖（如需开发）
cd ../frontend
npm install
npm run build
```

### 启动

```bash
# Windows
start.bat

# 或手动启动
cd backend
python main.py
```

访问 http://localhost:8000

## 使用流程

### 1. 上传弹道图片

支持 PNG/JPG 格式，自动识别绿色标记点。

### 2. 编辑弹道

| 操作 | 说明 |
|------|------|
| 右键拖动 | 平移画布 |
| 滚轮 | 缩放 |
| 点击 | 选中点 |
| Ctrl+点击 | 多选 |
| 框选 | 批量选择 |
| 方向键 | 微调（Shift 加速） |
| Ctrl+A | 全选 |
| Ctrl+Z / Y | 撤销 / 重做 |

选中多个点后显示八向缩放框，可拖动控制点缩放。

### 3. 导出配置

添加完所有枪械会生成lua脚本。

### 4. 使用脚本

1. 打开 **Logitech G HUB**
2. 选择鼠标 → **脚本**
3. 粘贴 `生成的lua`内容
5. 保存启用

## 按键配置

| 按键 | 功能 |
|------|------|
| G6 | 压枪开关（切换） |
| DPI+ | 下一把枪 |
| DPI- | 上一把枪 |
| 前进键 | 鼠标复位开关 |
| G9 | 配置复位 |

## 枪械配置示例

```lua
{
    name = "AK-47",
    rpm = 600,
    verticalMul = 1.0, --垂直倍率，可以根据改枪情况和灵敏度微调。
    horizontalMul = 1.0, --水平倍率
    pattern = {
        {y=13, x=0},    -- 第1发
        {y=26, x=-7},   -- 第2发
        {y=24, x=-5},   -- 第3发
        -- ...
    }
},
```

## CLI 工具

```bash
python pattern_generator.py <图片> [--scale-x 1.0] [--scale-y 1.0] [--debug]
```

## 预设数据

`data/` 目录包含预设弹道：

- `m14.lua` - M14 步枪
- `ash-12.lua` - ASH-12 步枪

### 贡献弹道数据

欢迎提交 PR 分享你调试好的弹道数据！

1. Fork 本仓库
2. 在 `data/` 目录添加 `<游戏>-<枪械名>.lua` 文件
3. 文件格式参考现有预设
4. 提交 PR 并注明游戏名称、枪械、测试环境（灵敏度等）

示例文件名：`cs2-ak47.lua`、`valorant-vandal.lua`、`apex-r301.lua`

## 技术栈

- **前端**: Vue 3 + TypeScript + Vite
- **后端**: FastAPI + OpenCV
- **脚本**: Lua (Logitech G HUB)

## 注意事项

- 本工具仅供学习研究使用
- 使用宏脚本可能违反某些游戏服务条款
- 请在训练场充分测试后使用

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

- **允许** - 复制、分发、修改
- **禁止** - 商业用途
- **要求** - 注明原作者

## 作者

Camvanaa @2026
