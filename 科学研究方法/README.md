# 科学研究方法：科学审美导师 Skill

一个 Claude Code / Claude skill，把 Claude 变成博士科研导师，训练你的**科学审美与独立研究判断力**，而不是替你总结论文或寻找 Research Gap。

## 它会做什么

1. 先帮你理解必要概念、研究问题和实验设计（只讲做判断必需的部分）。
2. **每次只提一个**关键科学判断题，你先回答，它再依据论文原文评价，不提前公布答案。
3. 围绕四个维度训练：研究重要性、证据支持范围、竞争性解释、可证伪性。
4. 主动寻找反对证据、允许你反驳，并区分【作者事实】【AI推断】【待验证假设】。
5. 多篇论文时引导你比较共同科学命题，不直接宣布 Research Gap。
6. 在 `judgment-log.md` 中记录你的判断与错误类型，定期回顾哪些能力真正提高。

## 文件结构

```
科学研究方法/
├── SKILL.md                         # 主指令（导师规则与流程）
├── references/
│   ├── judgment-dimensions.md       # 四个维度的题型、评价标准、错误分类
│   └── multi-paper.md               # 多篇论文比较的引导方法
└── templates/
    └── judgment-log.md              # 判断训练记录模板
```

## 安装

Claude Code（个人级，所有项目可用）：

```bash
mkdir -p ~/.claude/skills && cp -r 科学研究方法 ~/.claude/skills/scientific-taste-mentor
```

或项目级：复制到项目的 `.claude/skills/scientific-taste-mentor/`。

claude.ai：将本文件夹打包为 zip，在 Settings → Capabilities → Skills 中上传。

## 使用

```
/scientific-taste-mentor 带我精读这篇论文 <附上 PDF 或链接>
```

建议在一个固定的目录中使用，使 `judgment-log.md` 能跨会话累积，回顾功能才有意义。
