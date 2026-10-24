# 企业微信文件交付指南（wecom-cli）

前置：先加载 `wecomcli-shared` skill 完成公共检查，再按需加载 `wecomcli-media` 与 `wecomcli-message`。本指南只记录已验证的最短命令路径。

## 1. 前置检查

```bash
wecom-cli --version          # 版本须 ≥ 1.2.1
wecom-cli auth show --status # 输出 authorized 才能继续
```

- 未授权时按 wecomcli-shared 的流程初始化（展示二维码等待用户扫码），初始化完成后复查状态。
- 检查不通过则停止业务操作，把错误如实告知用户。

## 2. 发送"发到我企业微信"（给授权人本人）

用户说"发到我的企业微信/发给我"时，目标是**授权人本人**，无需 sessions list：

```bash
# 2.1 上传文件拿 media_id
wecom-cli media upload --json '{"file_path": "<本地文件绝对路径>"}'
#    → 返回 type=file 与 media_id（只内部使用，禁止展示给用户）

# 2.2 取授权人身份作为 chat_id
wecom-cli identity whoami
#    → 从 extra_identity_context 授权真人用户身份的 ID 字段取值（禁止展示给用户）

# 2.3 发送文件消息
wecom-cli message aibot send --json '{
  "chat_id": "<2.2 返回的授权人 ID>",
  "msg_type": "file",
  "file": {"media_id": "<2.1 返回的 media_id>"}
}'
#    → success:true 即送达
```

## 3. 发给其他会话（群聊/非授权人）

必须先 `wecom-cli message aibot sessions list`，在**本次返回**中按聊天名称唯一匹配后复制其 chat_id；多候选时列出让用户选（用名称+最后消息时间，不用 ID）。无匹配则停止，不得接受外部 ID。

## 4. 约束与失败处理

1. **ID 不外露**：chat_id / media_id / userid / msg_id 等一律只在命令中使用；最终回复用可读名称描述（"已发送到你本人的企业微信"）。
2. **错误 850002 / 850003**：机器人缺该项业务权限（附 help_message 与授权链接）——登录仍有效，**不要 reconnect_plugin**；原样转达 help_message，待用户确认授权后再重试原操作一次。
3. **连续发送**：同一流程内多次 send 不必重复 sessions list / whoami；但上下文被压缩后必须重新调用确保 chat_id 正确。
4. **文件路径**：中文路径可直接传入 JSON；路径必须真实存在，不得编造。
5. 每次请求只带一个与 msg_type 同名的内容对象（file 只传 file，markdown 只传 markdown）。

## 5. 典型交付组合

答辩 PPT 场景的完整交付 = PPTX 文件消息（第 2 节命令）＋一条简短 markdown 消息说明文件内容与页数（可选，正文 ≤20480 字节）。
