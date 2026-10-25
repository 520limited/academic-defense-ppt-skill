# 画布复现协议（从既有 .ardot 设计完整复现到新画布）

适用场景：用户给出一个既有 Ardot 设计文件（或要求"复现原来的 PPT"），要求在新画布上**逐节点忠实复现**——结构与数值 1:1，不做重新设计。本协议记录一次 22 页答辩 PPT 完整复现的验证过的流程，包含转录架构、并行纪律、导出前重排、溢出类缺陷修复四部分。

> 与"从零创作"的区别：从零创作先定大纲再画（见 `ardot-slides-recipe.md`）；复现是**纯转录**——原文件的每个节点属性原样搬到新画布，包括 `fill_container` / `hug_contents` 等自动布局字符串。复现的保真度标准 = 原设计结构，包括原设计自身的缺陷（是否修复见第 4 节）。

## 1. 数据转储（复现的唯一事实源）

对原文件逐页 dump 全深度节点数据，落盘为 JSONL（每行一个 slide 根的完整子树，含 children、fills、fontName、layout、gap、padding 等全部属性）。这份转储同时承担三个角色：转录输入、内容核对基准、残留清理时的查重依据。

```bash
# 分批读取避免超预算：按页段分批，每批 readDepth=-1
# 落盘：每行一个 SLIDE 节点的完整 JSON
```

## 2. 三层批协议（每页三个批次类型）

| 批次 | 内容 | 父级占位符 | 依赖 |
| --- | --- | --- | --- |
| fwa | slide 根节点 + PageHeader 子树 | page ID | 无，可首发 |
| fwb | 各 Band / Footer 根节点（仅自射属性） | `SLIDE_ID` | 需 fwa 返回的真实 slide ID |
| cN | 每 Band 的每个直接子级子树 | `BAND:<原BandID>` | 需 fwb 返回的真实 Band ID |

执行协议：

1. 发 fwa → **第一个返回节点 ID 就是真实 slide ID**，sed 替换 `SLIDE_ID` 后发 fwb。
2. fwb 返回的节点 ID 按 ops 顺序对应各 Band，sed 替换所有 cN 文件里的 `BAND:<原ID>`。
3. cN 内容批**各自独立、无跨批引用** → 可 4–5 批并行发送大幅提速。

子树 ops 数 > 25 时的拆分：先发"仅自射"批（父 = `BAND:<原ID>`），再按子级块发（父 = `BANDCH:<原ID>`）。绑定名按文件全局索引统一重命名（如 `x88_2001`），保证跨批不撞名。

## 3. 复现场景专属铁律

1. **转录不改设计**：`clean()` 只丢 `id`/`children`/`mainComponent` 等重建字段；`x/y == "auto"` 才丢弃（交给父级自动布局）；`fill_container`/`hug_contents` 字符串**必须原样保留**，不要手算成绝对值——手算正是溢出缺陷的来源（见第 4 节）。
2. **绑定名跨批即失效**：每批返回的 `expiredBindings` 明示这一点；内容批无跨批引用所以无害，但绝不能在第二批里引用第一批的绑定名。
3. **并行批的 ID 分配非确定**：并行发送时各批拿到交错的 ID 段（如批 A 得 4:629–4:653、批 B 得 4:579–4:603）。不影响内容正确性，但意味着**建页顺序 ≠ 层序 ≠ 页码顺序**，导出前必须重排（见第 5 节）。
4. **定高容器对照内容预算**：每个 fixed-height 容器，用 `内容自然高度 + 上下 padding` 核算是否装得下。装不下 = 原设计缺陷，转录时会 1:1 复刻出来。
5. **INSTANCE/COMPONENT 降级为 frame**：原文件里的组件实例在转录时按 `type:"frame"` 重建（子属性照搬），不保留实例关系。

## 4. 溢出类缺陷：诊断与修复

**症状**：capture_layout 报 `OUTSIDE_PARENT`（warning）——子节点超出父容器 bounds 且父级 `clipsContent: true`，有被裁剪切掉的风险。这是复现中最常见的一类真实缺陷。

**诊断**（不要凭子节点坐标猜父容器边界）：

```bash
capture_layout(fileUrl, parentId=<问题子节点的父容器ID>, problemsOnly=false, maxDepth=2)
```

返回父容器 bounds 与各子节点 bounds，直接比对。典型算例：

- KPI 带定高 110、padding 16、卡片内容高 95 → 需要 127，原设计少算 17px，卡底 1px 被裁。
- 自动布局列（fill_container）在定高 Band 内剩余 339px，7 行 hug 行（49px）+ 6 间隙（8px）= 391px → 末行完全不可见。

**修复原则**（按优先级）：

1. **撑高容器到"内容 + 标准 padding"**，不关 clipsContent、不挪内容——视觉位置不变，只补足原设计少算的高度。双侧并排 Band 要同步撑高保持齐底。
2. 撑高后确认不撞下游元素（Footer 通常在 y≈1000 局部，band 区上方有余量）。
3. 修复后对该页重跑 problemsOnly 扫描确认 `OUTSIDE_PARENT` 消失。

**良性警告识别**（不要误修）：

- `LARGE_EMPTY_AREA` / cause=`OversizedContainer`：容器大于内容的留白——徽章、横幅、标签框、KPI 卡的设计使然。
- `SIBLING_OVERLAP`：图表页中文本标签悬浮于**无填充的透明图表框**上——图层叠放设计。
- `MissingContent` 大面积空白：对照原设计 fwb 里 Band/Footer 的 y 与 height——若原设计 Band 本就只占页面上部、Footer 固定在底部，空白即设计使然。

## 5. 导出前必做：图层顺序重排

**PPTX 导出按图层面板顺序（层序）排列页面，不按传入的 nodeIds 顺序，也不按画布坐标。** 并行建页导致层序必然乱序（如 P02 排在 P01 前）。

重排方法：按目标顺序，把第 i 页（0-based）M 到 index=i。**按目标序号升序处理**，先放置的页不受后续移动影响：

```js
M(slideId_P01, pageId, 0)
M(slideId_P02, pageId, 1)
// ... 直到 N-1
```

一次 batch_edit 可放全部 N 个 M（N ≤ 25）。重排后 batch_read 页面子节点（readDepth=0）核对名称序列，再导出。

## 6. 残留碎片清理

废弃的早期重建尝试会在 page 级留下游离节点（占位文本、半成品 Band）。**删除前必须查重**：把每个残留节点的 name 与转储 JSONL 全文匹配，确认其内容已存在于最终某页 slide 内，才可 D() 删除；查不到的先保留并向用户说明，防止删掉唯一副本。

## 7. 数据核对（从 PPTX 侧回验）

复现完成后，从导出的 PPTX 反抽文本与基准对账：

```python
# zipfile 读 ppt/slides/slideN.xml，正则 <a:t>([^<]*)</a:t> 抽取全部可编辑文本
```

逐项核对基准数值（README / 正式报告）。**表示方式差异 ≠ 数据错误**：区间概括（"789 → 1302 MB"代替逐值）、四舍五入（13.60 → 13.6）、单位换算（"MP4 只有 WAV 的 30%"代替原始字节数）都是正常的设计取舍；只有**数值本身矛盾**才算问题。同时核对页面顺序：每页首文本应是该页标题（封面/目录/1.1/…/致谢）。

## 8. 导出对齐属性丢失与回填（关键陷阱）

**export_nodes(format=pptx) 会完整丢失全部段落的对齐属性**：画布上 100+ 个 `textAlignHorizontal=CENTER` 的文本（封面主标题、KPI 数字、卡片标题、图表说明行）导出后全部塌回 PowerPoint 默认的左对齐 + 顶锚定——slideN.xml 里 `algn=` 与 `anchor=` 一个都不剩。**框还是居中的框，但框内文字全部靠左站**，用户一眼就能看到"文字没对齐"。

**诊断**：解包 PPTX，`Counter(re.findall(r'algn="(\w+)"', xml))` 若为空字典即中招。

**回填方案**（`scripts/fix_pptx_align.py`，已验证幂等可重复跑）：

1. **提取画布对齐意图**：对每页 slide 节点 `batch_read(nodeIds=[slideId], readDepth=-1)`，下载返回的 JSONL，按树序收集每个 TEXT 节点的 `textAlignHorizontal`（LEFT/CENTER/RIGHT）与 `textAlignVertical`。**不要用坐标匹配**——自动布局内节点的 x/y 是 `"auto"`，且 hug 宽度的 CENTER 文本导出坐标本身就是左对齐计算值。
2. **按树序回填**：画布 TEXT 节点树序与 PPTX 每页 `<p:sp>` 顺序一一对应（导出保序，抽样验证过）。脚本逐 sp 消费对齐意图，在 `<a:pPr>` 注入 `algn="ctr"/"r"`、在 `<a:bodyPr>` 注入 `anchor`。**注意 run 级字符拆分不影响**（algn 是段落级属性）。
3. 每页若 `已回填数 ≠ 该页 TEXT 数`，报告数量不匹配并人工核对。
4. 重导后必须重跑回填（导出每次都丢）；回填脚本对已有 algn 幂等，可分页增量跑。

**画布侧的同类真缺陷**（回填修不了，因为是 LEFT 画错了）：用"同框内 LEFT 与 CENTER 并存"判据扫描全量结构——凡卡片/徽章/KPI 带内标题 LEFT 而说明文字 CENTER 的，把标题改 CENTER 统一（图表坐标轴标签、柱顶数值标签、散点标注的手动定位 LEFT 必须保留，动了就偏离数据点）。

**交付前最后一眼**：封面（主标题/徽章）、一页 KPI 带、一页矩阵卡，截图确认文字在各自容器内居中或对齐一致。
