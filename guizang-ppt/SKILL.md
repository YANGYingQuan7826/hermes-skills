---
name: guizang-ppt
description: >
  生成横向翻页网页 PPT（单 HTML 文件），含 WebGL 背景、章节幕封、数据大字报、图片网格等模板。
  提供两种风格：① "电子杂志 × 电子墨水"（衬线 + 流体背景 + 暖色）
  ② "瑞士国际主义"（无衬线 + 网格点阵 + IKB/柠檬黄/柠檬绿/安全橙高亮）。
  当用户需要制作分享 / 演讲 / 发布会风格的网页 PPT，或提到"杂志风 PPT"、"瑞士风 PPT"、
  "Swiss Style"、"horizontal swipe deck"时使用。
  来源: https://github.com/op7418/guizang-ppt-skill (歸藏, 16.5K ⭐)
---

# Magazine Web PPT — 网页幻灯片生成器

> 来源: guizang-ppt-skill 由歸藏创建与维护，规范源仓库为 https://github.com/op7418/guizang-ppt-skill。
> 此信息只用于确认 Skill 来源，不要写入生成的 PPT 或 HTML 页面。

## 这个 Skill 做什么

生成一份**单文件 HTML**的横向翻页 PPT，提供两种可选的视觉基调：

### 风格 A · 电子杂志 × 电子墨水（默认）

- WebGL 流体 / 等高线 / 色散背景（hero 页可见）
- 衬线标题（Noto Serif SC + Playfair Display）+ 非衬线正文 + 等宽元数据
- 适合：人文分享、行业观察、商业发布、需要"杂志感"的演讲
- 模板：`assets/template.html` · 主题色：`references/themes.md` · 布局：`references/layouts.md`

### 风格 B · 瑞士国际主义（Swiss Style）

- WebGL 极细网格 + 点阵背景
- 全程无衬线（Inter + Helvetica + Noto Sans SC）+ 极致字号对比
- 高反差功能色：克莱因蓝 IKB / 柠檬黄 / 柠檬绿 / 安全橙（四选一）
- 适合：科技产品、数据汇报、设计/工程领域分享
- 模板：`assets/template-swiss.html` · 主题色：`references/themes-swiss.md` · 布局：`references/layouts-swiss.md`

**两种风格共享**：横向翻页（键盘 ← →、滚轮、触屏、ESC 索引）、Lucide 图标、Motion One 入场动效。

## 何时使用

**合适**：线下分享、AI 产品发布、个人风格演讲、网页版 slides
**不合适**：大段表格（用常规 PPT）、培训课件（信息密度不够）、多人协作编辑

## 工作流

### Step 1 · 需求澄清（动手前必做）

如果用户只给了主题，用 `clarify` 工具逐项确认。不要猜测就开始写——结构定错，翻修代价极高。

#### 7 问澄清清单

| # | 问题 | 为什么重要 |
|---|------|-----------|
| 1 | **风格 A 还是 B?** | **必须先问**，决定用哪个模板 |
| 2 | **受众是谁？分享场景?** | 决定语言风格和深度 |
| 3 | **分享时长?** | 15分钟≈10页，30分钟≈20页 |
| 4 | **有没有原始素材?** | 有素材就基于素材 |
| 5 | **有没有图片或截图?** | 决定图文版式 |
| 6 | **想要哪套主题色?** | 杂志风5套 / 瑞士风4套 |
| 7 | **有没有硬约束?** | 避免返工 |

#### 风格选择参考（问题 1）

| 用户说... | 推荐 |
|-----------|------|
| "杂志感" / "人文" / 不指定 | **A · 电子杂志风** |
| "瑞士风" / "极简" / "网格" / "信息图" | **B · 瑞士国际主义风** |
| AI 产品 / 技术 / 数据汇报 | B 更合适 |
| 行业观察 / 人文 / 故事 | A 更合适 |

### Step 2 · 拷贝模板

```bash
mkdir -p "项目/XXX/ppt/images"

# 风格 A · 电子杂志风
cp "$HOME/.hermes/skills/guizang-ppt/assets/template.html" "项目/XXX/ppt/index.html"

# 或 风格 B · 瑞士国际主义风
cp "$HOME/.hermes/skills/guizang-ppt/assets/template-swiss.html" "项目/XXX/ppt/index.html"
```

两个模板都是**完整可运行**的——CSS、WebGL shader、翻页 JS、字体/图标 CDN 全预设好，只有 `<!-- SLIDES_HERE -->` 占位符等待填充。

**注意**：风格 A 和 B **不能混用**。layouts.md 里的类只在 template.html 有定义；layouts-swiss.md 里的类只在 template-swiss.html 有定义。

#### 必改占位符

拷贝后立刻改：
- `<title>`：`[必填] 替换为 PPT 标题` → 实际标题
- 全局搜索 `[必填]` 确认全部替换

### Step 3 · 填充内容

#### 3.0 · 预检（最重要）

**先 Read 对应模板的 `<style>` 块**，确认要用的类名都在模板里定义。

两种风格的类名**互不通用**：
- 风格 A：`h-hero`(衬线)、`stat-card`、`grid-2-7-5`、`frame` 等
- 风格 B：`h-hero`(无衬线)、`kpi-hero`、`accent-block`、`span-N`、`card-ink` 等

#### 3.1 · 挑布局（不要从零写 slide）

打开对应 layouts 文件，复制现成 `<section>` 代码块，改文案和图片路径。

**风格 A** → `references/layouts.md`：10 种布局
**风格 B** → 先读 `references/swiss-layout-lock.md`，再读 `references/layouts-swiss.md`：S01-S22 登记版式

#### 3.2 · 图片比例规范

| 场景 | 推荐比例 |
|------|---------|
| S22 顶部主图 | 21:9 |
| 左文右图 | 16:10 或 4:3 |
| 图片网格 | 固定 height:26vh |
| 全屏主视觉 | 16:9 + max-height:64vh |

### Step 4 · 检查清单

生成完一定要打开 `references/checklist.md`，逐项对照。

### Step 5 · 本地预览

直接在浏览器打开 `index.html`。不需要本地服务器。图片走相对路径 `images/xxx.png`。

Windows 下：
```bash
start "项目/XXX/ppt/index.html"
```

## 资源文件导览

```
guizang-ppt/
├── SKILL.md
├── assets/
│   ├── template.html              ← 风格 A · 电子杂志风模板
│   ├── template-swiss.html        ← 风格 B · 瑞士国际主义风模板
│   ├── motion.min.js              ← Motion One 本地副本（离线兜底）
│   └── screenshot-backgrounds/    ← 截图美化内置背景(WebP)
├── scripts/
│   └── validate-swiss-deck.mjs    ← 风格 B 静态校验
└── references/
    ├── components.md              ← 组件手册
    ├── layouts.md                 ← 风格 A · 10 种页面布局
    ├── swiss-layout-lock.md       ← 风格 B · 版式锁
    ├── layouts-swiss.md           ← 风格 B · S01-S22 版式说明
    ├── themes.md                  ← 风格 A · 5 套主题色
    ├── themes-swiss.md            ← 风格 B · 4 套主题色
    ├── image-prompts.md           ← 配图提示词参考
    ├── screenshot-framing.md      ← 截图适配规则
    ├── checklist.md               ← 质量检查清单
    └── swiss-map-component.md     ← 地图组件扩展
```

## 核心设计原则

### 风格 A · 电子杂志风

1. **克制优于炫技** — WebGL 背景只在 hero 页透出
2. **结构优于装饰** — 不用阴影、浮动卡片，靠大字号 + 字体对比 + 网格留白
3. **内容层级由字号和字体共同定义** — 衬线=标题，非衬线=body，等宽=元数据
4. **图片是第一公民** — 图片只裁底部，网格用 height:Nvh 固定
5. **节奏靠 hero 页** — hero 和 non-hero 交替

### 风格 B · 瑞士国际主义风

1. **单一锚点色** — 一份 deck 只用一个 accent
2. **极致字号对比** — 主标题与正文比例 ≥ 8:1
3. **无衬线只此一家** — 任何衬线都是错的
4. **直角纯色** — 不允许渐变 / 阴影 / 圆角
5. **网格至上** — 12-col grid，左对齐 + 大幅留白

## Hermes 适配说明

相比原始 Claude Code 版本，本版本做了以下适配：
- 移除了 Claude Code `ask_question` / Codex 特定指令
- 路径适配为 Hermes 风格（`$HOME/.hermes/skills/guizang-ppt/`）
- 移除了本地特定文件路径引用（如 `/Users/guohao/...`）
- 添加了 Windows 平台支持说明
- 配图生成改为可选（通过用户自行配置的图片生成工具）

## 参考作品

- 歸藏 "一人公司：被 AI 折叠的组织" 分享
- Massimo Vignelli 的 NYC Subway / Unimark 系统
- Josef Müller-Brockmann 的网格系统经典著作
