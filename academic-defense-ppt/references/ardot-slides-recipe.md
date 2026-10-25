# Ardot 高密度信息图 PPT 制作配方

动手前必读。本配方记录一套已验证的高密度信息图风格答辩 PPT 制作方法（N 页 16:9，N 由演讲时长推导，见 SKILL.md 输入参数表；全元素可编辑、零图片拼接），以及 12 条实战铁律——每条都对应一次真实的返工。

配方默认使用"学术蓝"皮肤。用户提供了其他风格参考图时：**结构与构建方法全部保留，仅替换第 1 节的 5 组色值**（主色/横幅渐变/浅底/描边/强调色），字体与字号体系可随参考图微调。

## 1. 风格规格（默认皮肤：学术蓝）

> 换肤方法：只改下表 5 组色值，其余结构、组件、构建模式不动。浅色卡片底/描边按主色同色系明度推导（主色混合 8–12% 白为浅底、混合 25–35% 白为描边）。

### 配色 Token（学术蓝皮肤取值）

| 用途 | 色值 |
| --- | --- |
| 主色（标题/编号/强调） | `#1A4FA0` |
| 横幅渐变 | `#2E66B5` → `#164B9E`（GRADIENT_LINEAR，左→右 transform `[[1,0,0],[0,1,0]]`） |
| 浅色卡片底 | `#F5F8FD` / `#EAF1FA` |
| 描边/分隔线 | `#C5D5EC` |
| 正文深灰 | `#3A4452` 附近 |
| 强调红（警示/异常值） | `#C00000` |
| 页底结论条文字 | `#1A1A1A` 黑粗体，前缀黑方块组件 |

### 字体

统一 **Noto Sans SC**。先用 get_available_fonts 确认可用样式名，再用精确的 family+style 组合：Regular / Medium / SemiBold / Bold / Black。字号体系：页头编号标题 28–32、横幅 24–26、带标题 22–24、正文 20、图表标注 16–18。信息图风格允许正文下探到 20px（参考图密度优先），但不得再小。

### 每页统一节奏

页首"编号+标题"蓝色粗体 + 勾选行导语 → 蓝色渐变横幅标题条 → 2–4 条浅蓝卡片内容带 → 页底"■ 结论："黑色粗体收束。

## 2. 画布初始化

1. `create_design` 建文件（文件名含主题与风格，如 `XXX_汇报_学术蓝信息图`）。
2. 所有 slide 放同一 page，网格排列：每行 5 页，`x = col × 2020`，`y = row × 1180`（页数任意，按 N 自动排布）。
3. slide 节点：`{type:"slide"}` 按编辑器 schema；16:9 比例画框（4:3 时同比例调整网格间距）。

## 3. 组件先行（在页头之前建好）

先建 5 个可复用组件，全部页面实例化引用，保证一致性：

| 组件 | 用途 | 结构 |
| --- | --- | --- |
| compCheck | 勾选行导语 | 蓝色 SVG 对勾 + 文本 |
| compSq | 页底结论前缀 | 黑色小方块 |
| compWave | 品牌声波图形 | 白色 SVG 波形（封面徽章用） |
| compArrow | 流程箭头 | 蓝色 SVG 箭头 |
| compArrowW | 横幅内白色箭头 | 同上换色 |
| PageHeader | 页头 | 3 个文本子节点：编号标题 / 勾选行文本 / 横幅标题 |

PageHeader 转组件：`U(pageHeaderId,{reusable:true})`。**注意：此操作会改变节点 ID**（如 `2:45` 变 `2:167`），后续引用用新 ID。

每页页头实例化 + 子文本覆写：

```js
hdr5 = I(slideId, {type:"ref", ref:"2:167"})
U(hdr5+"2:46",  {content:"3.2 实验环境与数据流"})   // 绑定拼接自动加 ";"，不要手写
U(hdr5+"2:53",  {content:"环境固定 · 数据流单向 · 结果可审计"})
U(hdr5+"2:55",  {content:"实验环境与数据流"})
```

**绑定拼接实例子路径**：`U(绑定名+子节点ID, {...})` —— 拼接运算自动插入 `";"` 分隔符。写成 `hdr5+";2:46"` 会产生 `;;` 双分号路径错误。

## 4. 每页构建模式

按带（band）组织，每页一次或两次 batch_edit 完成：

1. 页头实例 + 覆写（3 个 U）
2. 渐变横幅：frame + GRADIENT_LINEAR fills + 白色标题文本
3. 内容带：垂直 flex 容器 + 若干水平 flex 行（卡片 = 浅色底 + 圆角 + 描边）
4. 页底结论：黑方块组件实例 + 结论文本（Bold, #1A1A1A）

## 5. 图表绘制法（零图片拼接的核心）

所有图表 = **SVG 矢量几何 + 独立可编辑文本节点覆盖**：

- 插入 SVG：`I(parent,{type:"frame", svg:"<svg ...>...</svg>", name:"..."})`——SVG 会被解析成 frame + vector 子节点。
- 坐标轴、网格线、柱条、折线、散点全部画进 SVG（按数据线性映射像素坐标，先算好再写）。
- **轴标签、数值标注、图例全部用独立 TEXT 节点**叠加在 SVG 上方（文本可编辑是硬要求，不能烙进 SVG）。
- 常见图表实现：柱状图（rect 组）、折线（polyline + circle 数据点）、散点（circle 组 + 虚线前沿 polyline `stroke-dasharray`）、分组柱（按类别偏移 x）。
- Y 轴标签等负偏移元素注意父级边界，避免 OUTSIDE_PARENT（轴标签放图框内部 x≥8 处，不要用负 x）。

## 6. 十二条实战铁律

1. **绑定名绝不跨调用复用**：每次 batch_edit 的所有操作行使用全新绑定名（用页码前缀，如 `p15cap`、`p15rc`）。复用旧名会连续 internal_error 且难以定位。
2. **每次 ≤25 个操作**：按逻辑分批（页头一批、内容带一批、图表一批）。
3. **绑定拼接自动加 ";"**：`U(hdr5+"2:46",...)`，不要手写分号。
4. **flex 父级忽略子节点 x/y**：绝对定位需显式 `layoutPositioning:"ABSOLUTE"`；否则用 flex 对齐（如居中箭头做成 `layout:"horizontal", width:"fill_container", primaryAxisAlignItems:"CENTER"` 的包裹 frame）。
5. **Copy 的 descendants 键用原子路径**：普通 frame 复制后子 ID 全部重新生成，`C(id,parent,{descendants:{旧子ID:...}})` 会失败——先 Copy 再 batch_read 拿新子 ID 后 U()。组件实例（ref）的 descendants 才可用原子路径直改。
6. **U(node,{reusable:true}) 会改节点 ID**：转组件后立刻记录新 ID。
7. **插入顺序即排列顺序**：后补的元素会追加到容器末尾。错了用 Move 修正：`M(nodeId,parentId,index)`（如把三个箭头移到 1/3/5 位插入四个流程框之间）。
8. **文本节点必须显式 fill**：文本默认无色；颜色用 `fill:"#RRGGBB"` 或 fills SOLID。
9. **禁用 Unicode 符号图标**：✓ ■ → 等字符在文本节点中渲染不可控，图标一律 SVG frame / 组件实例。
10. **渐变 fills 的 gradientStops 每项**含 color+position；gradientTransform 二维矩阵按方向查表（左→右 `[[1,0,0],[0,1,0]]`，上→下 `[[0,1,0],[-1,0,1]]`）。
11. **尺寸语义**：`hug_contents` 收缩包裹、`fill_container` 撑满父级（父级需有 layout）、`fill_container(200)` 带最小值。文本行高默认 AUTO，密集排版用 PIXELS 指定行高。
12. **capture_layout 对 page 根节点报 "Root node must be a container"**：传单页 slide 节点 ID，不传 page ID。修复优先级：溢出/重叠 > 空白面积警告。

## 7. 验证与修复流程

1. 每页完成 → capture_layout（parentId=该页 ID，problemsOnly=true，maxDepth 适当）。
2. 按问题清单一次性修复（一批 batch_edit，全新绑定名）。
3. 关键页（封面、最密页、全部图表页、表格页）用 capture_screenshot 做一次集中视觉审查（一次调用传全部目标页 ID，≤10 个）。
4. 下载截图逐张分析，提取**全部**问题后一批修完，最多再截一次复查。

## 8. 导出

- export_nodes(format="pptx", nodeIds=[全部 slide ID]) → 临时签名 URL（有时效）。
- 立即 curl 下载到项目目录；文件名建议与画布同名。
- 用 `scripts/verify_pptx.py` 校验（页数/文本/媒体=0/关键内容抽查）。
