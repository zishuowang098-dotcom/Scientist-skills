# Zotero ↔ Codex 桥接：用 ChatGPT 登录在 Zotero 里翻译、解析、科学审美训练

**思路**：Zotero 的 AI 插件都需要一个 "OpenAI 兼容接口 + API Key"。本工具在你电脑上启动一个本地服务（`http://127.0.0.1:8765/v1`），把插件的请求转给你已经用 **ChatGPT 账号登录的 Codex CLI**（`codex exec`）。因此：

- 不需要 OpenAI API Key，不按 token 另付费；消耗的是 ChatGPT 套餐里的 **Codex 使用额度**（有上限，高强度使用可能触发限额）。
- Codex 会自动加载你已安装的 `scientific-taste-mentor` 技能（Codex 版，见 `../codex/scientific-taste-mentor/`）。
- 服务只监听本机，论文内容经由 Codex 发送给 OpenAI，与直接用 Codex 相同。

```
Zotero 插件 ──HTTP──▶ bridge.py (本机 8765) ──▶ codex exec (ChatGPT 登录) ──▶ OpenAI
```

> 代价：每次请求都要启动一次 Codex，**响应比直接调 API 慢**（通常几秒到几十秒）。所以划词即时翻译建议用免费引擎，Codex 用于高质量翻译、解析和导师模式。

## 提供的"模型"

在插件的 Model 栏填写以下名字之一：

| 模型名 | 用途 | Codex 权限 |
|--------|------|-----------|
| `codex-translate` | 学术翻译（英⇄中），只输出译文，低推理强度、较快 | 只读 |
| `codex-explain` | 解析不懂的概念/句子/公式，区分原文与推断 | 只读 |
| `codex-mentor` | 调用科学审美导师 skill，一次一题训练，记录写入 `~/ScienceMentor/research-training/judgment-log.md` | 仅可写工作目录 |
| `codex` | 通用对话 | 只读 |

可用 `模型名:底层模型` 指定 Codex 用哪个模型，例如 `codex-mentor:gpt-5.5`；不写则用 Codex 默认配置。

## 第一步：确认 Codex 和 skill 就绪

```bash
codex login status
```

若未登录，运行 `codex login` 并选择 **Sign in with ChatGPT**。

确认 Codex 版 skill 已安装（应能看到 SKILL.md）：

```bash
ls ~/.agents/skills/scientific-taste-mentor/
```

如果还没装，按 [`../codex/scientific-taste-mentor/README.md`](../codex/scientific-taste-mentor/README.md) 安装（用户级，所有目录可用）。

可以先在终端里直接测试一次：

```bash
echo '用 $scientific-taste-mentor 技能，告诉我你会怎样带我读论文' | codex exec --skip-git-repo-check -
```

## 第二步：启动桥接

需要 Python 3.8+（无需安装任何第三方包）。

- **macOS**：首次在终端执行 `chmod +x start-mac.command`，之后双击 `start-mac.command`
- **Windows**：双击 `start-windows.bat`
- 或在终端：

```bash
python3 bridge.py --port 8765
```

看到 `桥接已启动：http://127.0.0.1:8765/v1` 即可。用 Zotero 时保持这个窗口开着。

自测（另开一个终端）：

```bash
curl http://127.0.0.1:8765/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"codex-translate","messages":[{"role":"user","content":"Attention is all you need."}]}'
```

常用参数：`--token 某个字符串`（要求插件 API Key 填同样的值，防止本机其他程序调用）、`--workdir` 训练记录存放目录、`--timeout` 超时秒数、`--codex` 指定 codex 路径（Zotero/启动脚本找不到 codex 时用）。

## 第三步：在 Zotero 中配置

### A. 对话、解析、导师模式：llm-for-zotero（推荐）

[llm-for-zotero](https://github.com/yilewang/llm-for-zotero) 支持 Zotero 7 和 8，可以针对当前打开的 PDF 对话。

1. 从其 GitHub Releases 下载 `.xpi`，Zotero → 工具 → 插件 → 齿轮 → Install Plugin From File。
2. 在插件设置中新增 Provider：
   - 协议选择 **OpenAI Chat Completions 兼容**（`openai_chat_compat`，不要选 Responses API）
   - API Base URL：`http://127.0.0.1:8765/v1`
   - API Key：`--token` 的值；没设置就随便填，如 `local`
   - Model：分别添加 `codex-explain`、`codex-mentor`、`codex-translate`
3. 点 Test Connection。
4. 使用：选中不懂的段落 → 切到 `codex-explain` 提问；要训练判断力时切到 `codex-mentor`，说"带我精读这篇论文"。

同类插件 [zotero-ai-sidebar](https://github.com/xuhan-rgb/zotero-ai-sidebar) 也支持自定义 OpenAI 兼容地址，填法相同。

### B. 划词翻译：Zotero PDF Translate

[Translate for Zotero](https://github.com/windingwind/zotero-pdf-translate)：

- 日常即时翻译：用其内置的免费引擎（Google / Bing / 有道等），速度快且不占 Codex 额度。
- 需要高质量学术翻译时：在翻译服务中选 ChatGPT / 自定义 GPT（各版本名称略有不同），接口地址填 `http://127.0.0.1:8765/v1/chat/completions`（若该项要求填 Base URL 则填 `http://127.0.0.1:8765/v1`），模型填 `codex-translate`，API Key 同上。

## 导师模式的使用说明

- 每次请求都会把插件里的**完整对话历史**交给 Codex，所以"一次一题 → 你作答 → 评价"的多轮训练可以正常进行。
- 训练记录固定为 `~/ScienceMentor/research-training/judgment-log.md`（可用 `--workdir` 改），跨会话累积，回顾功能依赖它。桥接会把这个路径直接告诉 skill，所以它不会每轮都问你存哪里。若想与在 Codex 里直接训练时共用一份记录，把 `--workdir` 设成那个科研项目的根目录。
- 让插件把论文全文或相关段落带进对话（llm-for-zotero 的 PDF 上下文功能），否则导师会按 skill 规则要求你提供原文。

## 常见问题

| 现象 | 处理 |
|------|------|
| 启动时提示找不到 codex | 用 `--codex` 指定完整路径（macOS 用 `which codex` 查；Windows 用 `where codex`） |
| 插件报 502，日志里有 401/未登录 | 重新 `codex login`；Codex 登录过期 |
| 插件报 502，日志里提到 usage limit | ChatGPT 套餐的 Codex 额度用完，等待重置 |
| 插件等待超时 | 插件自身超时较短；导师模式推理强度高，可在插件里调大超时，或改用 `codex-explain` |
| 插件只支持 Responses API | 本桥接只实现了 Chat Completions；选择插件里的 OpenAI 兼容/Chat Completions 选项 |

## 说明与限制

- 这不是 OpenAI 官方 API，只是在本机调用 Codex CLI。请遵守 OpenAI 的使用条款，仅供个人在本机使用，不要把服务暴露到局域网或公网。
- 为了安全，翻译/解析模式下 Codex 以只读沙箱运行，并被要求不执行命令；导师模式只能写入工作目录。PDF 中的文本理论上可能包含诱导模型执行操作的内容，沙箱限制了其影响范围。
- 图片（如插件发送的截图）会通过 `codex exec -i` 附上。
