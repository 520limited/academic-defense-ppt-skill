# academic-defense-ppt-skill

WorkBuddy Skill：学术答辩 PPT 全流程制作与交付。（个人自用分享）

从一份完整的实战流水线沉淀而来，已参数化：用户提供参考风格图 + 内容资料（讲稿、实验数据、正式报告 docx），按指定的**演讲时长 T 分钟 / 页数 N**，一条链路产出：

- **N 页 16:9 高密度信息图风格汇报 PPT**（默认"学术蓝"皮肤，可换肤；Ardot 画布制作，全元素可编辑、零图片拼接；交付 .ardot 设计稿，不导出 PPTX）
- **数据核对**：PPT 与演讲稿中的每个数字逐项对照正式报告，口径矛盾如实上报
- **演讲稿 Word 文档**：与 PPT 逐页对应、按 `(T−2) × 170 / N` 字核算每页口播、附备答速查表
- **企业微信交付**：wecom-cli 文件消息直达用户本人

时长与页数规则：页数默认取 `T × 0.7`（30 min ≈ 22 页，10 min ≈ 7–8 页）；每页口播字数 = `(T − 2) × 170 / N`；2 分钟为翻页与答疑弹性。

## 安装

将 `academic-defense-ppt/` 目录复制到 WorkBuddy 的用户技能目录：

```
~/.workbuddy/skills/academic-defense-ppt/
```

重启 WorkBuddy 会话后即可被触发（说"参照参考图做一份答辩 PPT"等即可命中）。

## 目录结构

```
academic-defense-ppt/
├── SKILL.md                              # 主流程：7 阶段流水线 + 通用铁律
├── scripts/
│   └── extract_docx_text.py              # docx 全文+表格提取（标准库，无依赖）
└── references/
    ├── ardot-slides-recipe.md            # Ardot 信息图配方（默认学术蓝皮肤，可换肤）+ 12 条实战铁律
    ├── data-audit-and-speech.md          # 数据核对清单 + 演讲稿结构模板 + Word 生成命令
    └── wecom-delivery.md                 # wecom-cli 交付命令流与失败处理
```

## 变更记录

- 2026-10-25：**移除"PPTX 导出与校验"阶段**。Ardot 导出器对中西文混排文本会丢弃中文段（纯中文 / 纯拉丁文本正常），导出物不可用；交付改为以 .ardot 设计稿为准，并删除 `scripts/verify_pptx.py`。

## 核心铁律（摘录）

1. **绑定名绝不跨调用复用**——每次 batch_edit 用全新绑定名前缀，否则 internal_error。
2. **零图片拼接**——图表全部 SVG 矢量几何 + 独立可编辑文本节点，交付 .ardot 设计稿（不做 PPTX 导出）。
3. **数据诚实**——所有定量结论可溯源到原始记录；实测与假设不符时如实呈现。
4. **截图稀缺**——capture_screenshot 每修复批次 ≤2 次，禁止增量循环截图。
5. **ID 不外露**——接口返回的内部标识只用于调用，最终回复用可读名称。

## 依赖环境

- WorkBuddy（Ardot 画布 MCP + 本地 editor_sdk）
- Python 3.10+（脚本仅用标准库）
- wecom-cli ≥ 1.2.1（企业微信交付阶段）

## License

MIT
