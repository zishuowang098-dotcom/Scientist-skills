# 科学研究方法：科学审美导师 Skill（Claude Code / claude.ai 版）

把 Claude 变成博士科研导师，训练你的**科学审美与独立研究判断力**，而不是替你总结论文或寻找 Research Gap。
Codex 版见仓库中的 `codex/scientific-taste-mentor/`。

## 它会做什么

1. **两种模式分开**：你不懂的概念（如 PSD、PLV、对比学习），先在解释模式中直接讲清楚，并结合论文图表说明其作用；理解之后再进入判断训练。
2. **先核查，再评价**：每篇论文先报告实际读取范围，再为核心主张建立证据核查表（实验、图表、统计、对照），然后才出题和评价。未读到的材料只标【未核验】，不得用作评价依据。
3. 判断训练中**每次只提一个**关键科学判断题，你先回答，它再依据原文评价，不提前公布答案。
4. 围绕四个维度训练：研究重要性、证据支持范围、竞争性解释、可证伪性。
5. 区分【原文结果】【作者解释】【AI推断】【待验证假设】【未核验】；不把模型性能当作机制证据，也不把某一种解释表述为已证实的机制。
6. 多篇论文时引导你比较共同科学命题，检查证据是否真正独立，不直接宣布 Research Gap。
7. 在**固定路径**的训练记录中追踪能力层级：L1 独立判断 → L2 支持与反对证据 → L3 区分性实验，以及每次需要多少提示。

## 文件结构

```
科学研究方法/
├── SKILL.md                         # 主指令（模式、规则、证据核查、流程、记录位置）
├── references/
│   ├── judgment-dimensions.md       # 能力层级、四个维度的题型与错误分类
│   └── multi-paper.md               # 多篇论文比较的引导方法
└── templates/
    └── judgment-log.md              # 训练记录模板（能力层级优先）
```

## 安装

Claude Code（个人级，所有项目可用）：

```bash
git clone https://github.com/zishuowang098-dotcom/scientist-skills
mkdir -p ~/.claude/skills/scientific-taste-mentor
cp -r scientist-skills/科学研究方法/. ~/.claude/skills/scientific-taste-mentor/
ls ~/.claude/skills/scientific-taste-mentor/   # 应直接看到 SKILL.md、references、templates
```

注意写法是 `科学研究方法/.`（带结尾的 `/.`）。如果写成 `cp -r 科学研究方法 目标目录`，而目标目录已经存在，文件会被复制成 `目标目录/科学研究方法/SKILL.md` 这样的嵌套结构，Claude 将找不到 skill。

更新到新版本：

```bash
cd scientist-skills && git pull && cp -r 科学研究方法/. ~/.claude/skills/scientific-taste-mentor/
```

项目级安装：复制到项目的 `.claude/skills/scientific-taste-mentor/`。

claude.ai：将本文件夹的内容打包为 zip（SKILL.md 位于 zip 内的顶层文件夹中），在 Settings → Capabilities → Skills 中上传。

## 使用

```
/scientific-taste-mentor 带我精读这篇论文 <附上 PDF 或链接>
```

训练记录默认存放在科研项目根目录下的 `research-training/judgment-log.md`（git 仓库取仓库根目录，否则取当前目录），创建前会先向你确认路径。建议始终在同一个科研项目目录中使用，这样跨会话的能力回顾才有意义。
