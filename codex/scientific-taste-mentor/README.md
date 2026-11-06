# 科学审美导师 Skill（Codex 版）

与 Claude 版（`科学研究方法/`）内容一致，规则、证据核查、能力层级和训练记录格式相同。区别只有：

- 调用方式为 `$scientific-taste-mentor`（或在 Codex 中运行 `/skills` 选择）。
- `SKILL.md` 增加了"在 Codex 中运行的注意事项"：出完一题就结束本轮回复、只读不改论文、PDF 文本提取与读取范围记录、写记录前确认路径。
- 增加 `agents/openai.yaml`，提供在 Codex 界面显示的名称、简介和默认提示词。

## 安装

用户级（所有项目可用）：

```bash
git clone https://github.com/zishuowang098-dotcom/scientist-skills
mkdir -p ~/.agents/skills/scientific-taste-mentor
cp -r scientist-skills/codex/scientific-taste-mentor/. ~/.agents/skills/scientific-taste-mentor/
ls ~/.agents/skills/scientific-taste-mentor/   # 应直接看到 SKILL.md、agents、references、templates
```

仓库级：复制到科研项目中的 `.agents/skills/scientific-taste-mentor/`。

Codex 通常会自动发现新 skill；如果没有出现，重启 Codex。

## 使用

```
$scientific-taste-mentor 带我精读这篇论文 paper.pdf
```

训练记录默认存放在项目根目录的 `research-training/judgment-log.md`。如果同时使用 Claude 版和 Codex 版，在同一个科研项目里它们会读写同一份记录。
