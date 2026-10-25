---
name: academic-defense-ppt
description: 学术答辩 PPT 全流程制作与交付技能。当用户需要"参照参考图片/资料制作答辩用 PPT/汇报 PPT"、"PPT 要求全元素可编辑、不能图片拼接"、"做好的 PPT 发到企业微信"、"根据正式报告生成演讲稿"时使用。覆盖完整链路：参考风格分析 → 大纲与时间分配 → Ardot 画布高密度信息图制作 → 质量验证 → PPTX 导出与校验 → 数据与正式报告核对 → 演讲稿 Word 生成 → 企业微信文件交付。
agent_created: true
---

# 学术答辩 PPT 全流程（Ardot 信息图 → PPTX → 企业微信）

本技能源自一次完整的实战流水线，已参数化：用户提供参考风格图 + 内容资料（讲稿、实验数据、正式报告 docx），按指定的**演讲时长 T 分钟 / 页数 N** 产出 N 页 16:9 高密度信息图风格答辩 PPT（默认"学术蓝"皮肤，可整体换肤；全部元素可编辑、零图片拼接）、一份与 PPT 逐页对应的演讲稿 Word 文档，并通过企业微信发送给用户。

## 输入参数（阶段 0 一次问清，之后不再就方案性问题反复打扰）

| 参数 | 取值规则 | 说明 |
| --- | --- | --- |
| 演讲时长 T | 优先取用户原话；未提则按 N × 1.3 分钟反推并告知 | 决定每页口播字数与内容深度 |
| PPT 页数 N | 用户指定；未指定则建议 T × 0.7 取整（30 min ≈ 22 页，10 min ≈ 7–8 页） | 大纲与画布制作的总量基准 |
| 画幅 | 16:9（默认）或 4:3 | 影响画框尺寸与网格间距 |
| 风格皮肤 | 默认学术蓝；用户给了参考图则以参考图为准 | 换肤 = 替换配方中 5 组色值，结构不变 |
| 演讲稿 | 默认生成 | 可只要 PPT |
| 交付渠道 | 默认企业微信；也可仅本地文件 | 影响阶段 8 是否执行 |

## 何时使用

- 用户给出参考图片（如高校信息图风格 PPT 截图）并要求"完全参照该风格制作汇报 PPT"
- 用户要求 PPT "所有元素可编辑，不得使用图片拼接"
- 用户要求"做完发到我企业微信"
- 用户要求"根据正式报告生成演讲稿"，且指定"所有数据以报告为准"
- **复现场景**：用户给出既有 .ardot 设计文件（或"复现原来的 PPT"），要求在新画布逐节点忠实复现 → 先读 `references/reproduction-protocol.md`

## 总流程（8 个阶段）

| 阶段 | 产出 | 关键工具 |
| --- | --- | --- |
| 0 需求确认 | 大纲与画幅确认 | AskUserQuestion（一次问清：大纲确认、16:9/4:3） |
| 1 素材读取 | 结构化内容清单 | Read；报告 docx 用 `scripts/extract_docx_text.py` |
| 2 大纲设计 | slide-outline.md | 逐页标题 + 布局 + 时间分配 + 风格规格 |
| 3 画布制作 | N 页 .ardot 设计稿 | 先读 `references/ardot-slides-recipe.md`，再 create_design + batch_edit |
| 4 质量验证 | 布局问题清零 | capture_layout(problemsOnly) 每页；capture_screenshot 稀缺使用 |
| 5 导出校验 | .pptx 本地文件 | export_nodes(pptx) → curl 下载 → `scripts/verify_pptx.py` |
| 6 数据核对 | 核对结论 + 矛盾清单 | PPT 数字逐项对照报告；矛盾如实报告用户，不擅自统一 |
| 7 演讲稿生成 | 演讲稿 .docx | 读 `references/data-audit-and-speech.md`，edsdk 建 doc 写入 |
| 8 企业微信交付 | 用户收到文件 | 读 `references/wecom-delivery.md`，wecom-cli 三步走 |

**按顺序执行；用户中途追加需求（如演讲稿）时，从对应阶段切入，但必须先做阶段 6 的数据核对。**

## 阶段要点

### 阶段 0：需求确认（一次问清，不反复追问）

用一次 AskUserQuestion 确认：① 大纲/页数与时间分配是否认可（给出建议方案，页数按上表规则推导）；② 画幅 16:9（推荐）或 4:3。用户确认后不再就方案性问题反复打扰。

### 阶段 1：素材读取

- 讲稿类 markdown、README 数据表直接 Read。
- 正式报告 docx：运行 `python scripts/extract_docx_text.py "<docx路径>" -o report_extract.txt`，得到含表格的全文，作为**数据唯一基准**。

### 阶段 2：大纲设计

产出 `slide-outline.md`，包含：Meta（主题/场景/风格/页数 N/时长 T）、逐页大纲（页码、标题、内容要点、布局模式、是否含图表）、**时间分配表**、视觉节奏说明。

时间核算公式（按中文语速 170 字/分钟）：

- 每页口播字数 ≈ `(T − 2) × 170 / N`（2 分钟为翻页停顿与答疑过渡弹性）
- 时间分配表按部分（封面/章节/结论）汇总，合计 = T − 2；各部分页数占比 ≈ 时间占比
- 页面深度参考：1.5 分钟页 ≈ 250 字口播 + 2–4 个信息块；0.5 分钟页（封面/过渡/致谢）不塞内容

### 阶段 3：画布制作（先读配方再动手）

**动手前必须完整阅读 `references/ardot-slides-recipe.md`**——其中包含高密度信息图的完整规格（配色 Token、字体、组件系统、每页构建模式、图表绘制法）和 12 条实战铁律。违反任何一条铁律都会导致 batch_edit 报错或返工。配方默认"学术蓝"皮肤；用户提供了其他风格参考图时，保持配方中的结构与构建方法，仅替换 5 组色值（主色/横幅渐变/浅底/描边/强调色）。

**复现模式**（从既有 .ardot 复现）改读 `references/reproduction-protocol.md`：三层批协议（fwa/fwb/cN 占位符替换）、并行提速与绑定名纪律、转录时 `fill_container`/`hug_contents` 原样保留不手算。

### 阶段 4：质量验证

- 每页完成后对单页 slide 节点跑 capture_layout（problemsOnly=true），修复 OUTSIDE_PARENT 溢出、文本重叠。
- **OUTSIDE_PARENT 诊断**：对该节点的父容器跑 capture_layout（problemsOnly=false, maxDepth=2）取实际 bounds 比对；修复优先撑高父容器到"内容 + 标准 padding"（双侧并排 Band 同步撑高），不关 clipsContent、不挪内容。
- **良性警告不修**：OversizedContainer 留白、图表页标签叠透明图表框的 SIBLING_OVERLAP、原始设计固有的底部 MissingContent（对照 fwb 的 Band/Footer 位置确认）。
- capture_screenshot 是稀缺资源：**每修复批次最多 2 次**，且必须在当批所有修复完成后一次性截取。截图仅作内部验证，不得作为交付物。

### 阶段 5：导出与校验

1. **导出前重排图层顺序**（复现模式必做，并行建页会导致层序乱序）：按目标顺序把第 i 页 M 到 index=i（升序处理，一次 batch_edit ≤25 ops），batch_read 核对名称序列。
2. export_nodes：传入全部 slide 节点 ID，format=pptx，获得临时签名 URL。
3. curl 下载到项目目录（URL 有时效，立即下载）。
4. **对齐属性回填（关键，每次导出后必做）**：PPTX 导出会完整丢失全部段落的 algn/anchor——画布上所有 CENTER 文本导出后全部变左对齐。诊断：解包后 `re.findall(r'algn="(\w+)"', xml)` 为空即中招。修复：运行 `python scripts/fix_pptx_align.py "<pptx路径>" <各页结构JSONL>`——先对每页 slide batch_read(readDepth=-1) 拿树序结构，脚本按树序向 `<a:pPr>` 注入 algn（画布 TEXT 节点树序与 PPTX 每页 sp 顺序一一对应）。**重导后必须重跑**（幂等，可分页增量）。
5. **画布侧对齐体检**：扫描"同框内 LEFT 与 CENTER 并存"的卡片（脚本判据见复现协议第 8 节），把标题统一为与说明文字一致的 CENTER；图表轴标签/柱顶数值/散点标注的手动 LEFT 保留。
6. 运行 `python scripts/verify_pptx.py "<pptx路径>" --slides <N>` 校验：页数、总文本节点数、图片素材数（全可编辑要求 media=0）、可传入 `--expect "关键词1" "关键词2"` 抽查关键内容。
7. 从 PPTX 反抽文本（zipfile + 正则 `<a:t>`）做页面顺序与关键数值回验。

### 阶段 6：数据核对

以报告提取文本为基准，逐项核对 PPT/演讲稿中的每个数字（环境配置、各组实验关键值、结论数字）。**发现口径矛盾（如报告写"三次重复"、README 写"5 次"）时：如实告知用户并建议修改报告，产出物中使用"重复测量多次"等稳妥表述规避，绝不擅自替用户统一口径。**

### 阶段 7：演讲稿生成

读 `references/data-audit-and-speech.md`：演讲稿结构模板（时间轴总览 + 逐页口播 + 备答速查表）、语速核算公式（每页字数 = (T−2) × 170 / N）、edsdk 生成 Word 的确切命令。

### 阶段 8：企业微信交付

读 `references/wecom-delivery.md`：wecom-cli 前置检查 → media upload → identity whoami → message aibot send 三步命令与失败处理。注意：所有内部 ID（chat_id/media_id/userid）只用于调用，**最终回复中禁止出现**。

## 通用铁律（所有阶段生效）

1. **数据诚实**：所有定量结论必须有原始记录支撑；未实测的数值标注"待填充"，绝不编造。
2. **全元素可编辑**：图表用 SVG 矢量几何 + 可编辑文本节点，禁用位图拼接；导出校验 media 数必须为 0。
3. **绑定名唯一**：每次 batch_edit 使用全新绑定名前缀（如 p15cap、p15rc），绝不跨调用复用。
4. **无 Unicode 符号图标**：文本节点禁用 ✓ ■ → 等 U+2300–27BF 字符，图标一律用 SVG frame 或组件。
5. **截图稀缺**：capture_screenshot 每修复批次 ≤2 次，禁止增量循环截图。
6. **ID 不外露**：企业微信等接口返回的内部标识不得出现在最终回复中，用可读名称指代。
