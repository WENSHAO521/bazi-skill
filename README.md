![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)
![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)

# 赛博算命 Skill

基于 Claude Code 的综合命理分析工具。通过交互式对话收集信息，参照传统典籍进行专业分析。目前支持**八字（四柱）**与**测字（拆字）**，紫薇斗数、六爻、奇门遁甲、姓名学等更多方法正在规划中。

## 功能

- **统一入口** — 一个 skill 覆盖多种命理方法，未指明方法时会先询问用户想用哪一种
- **八字（四柱）** — 逐步收集姓名、阳历/农历生日、出生时辰、性别、出生地等信息，自动排出年柱、月柱、日柱、时柱，计算大运与流年，结合九本经典典籍进行日主强弱、十神关系、五行平衡、格局判定、大运流年解读及综合建议
- **测字（拆字）** — 只需一个汉字和想问的事情，结合传统拆字技法（增笔、减笔、拆字、会意、象形、谐音、假借、参形）做趣味解读
- **持续扩展** — 后续计划加入紫薇斗数、六爻（摇卦/纳甲）、奇门遁甲、姓名学（五格剖象）

## 安装

> **注意**：Claude Code 从 git 仓库根目录的 `.claude/skills/` 查找 skill，请在正确的位置执行。八字方法需要本机安装 `python3`（只用标准库，无额外 pip 依赖）；测字方法无额外依赖。

```bash
# 安装到当前项目（在 git 仓库根目录执行）
mkdir -p .claude/skills
git clone https://github.com/jinchenma94/bazi-skill .claude/skills/mingli

# 或安装到全局（所有项目都能用）
git clone https://github.com/jinchenma94/bazi-skill ~/.claude/skills/mingli
```

## 使用

在 Claude Code 中输入以下任意关键词即可触发：

`算命` `命理` `占卜` `算八字` `看八字` `批八字` `排八字` `四柱` `命盘` `排盘` `bazi` `测字` `拆字` `相字`

如果只是笼统地说"算命"、"看看运势"，skill 会先询问你想用八字还是测字。若明确说出了方法（如"帮我测个字"），会直接进入对应流程。

八字流程确认出生信息后会执行（依赖本机 **python3** 3.6+，只用标准库）：

```bash
python3 methods/bazi/scripts/pai_pan.py --solar 1990-05-15 --shichen 午 --sex 男
```

测字流程不需要脚本计算，只需一个汉字和想问的事情即可开始。

## 参考典籍（八字部分）

| 典籍 | 简称 |
|------|------|
| 《穷通宝典》 | 论日主调候 |
| 《三命通会》 | 论格局神煞 |
| 《滴天髓》 | 论五行旺衰 |
| 《渊海子平》 | 论十神六亲 |
| 《千里命稿》 | 论命例实证 |
| 《协纪辨方书》 | 论择日神煞 |
| 《果老星宗》 | 论星命合参 |
| 《子平真诠》 | 论用神格局 |
| 《神峰通考》 | 论命理辨误 |

测字部分参照《测字秘牒》《相字心易补遗》一类民间典籍记载的拆字技法整理，详见 `methods/celizi/references/chaizi-fa.md`。

## 项目结构

```
bazi-skill/
├── SKILL.md                                # Skill 入口（路由：确定用户想用哪种方法）
├── methods/
│   ├── bazi/                               # 八字（四柱）
│   │   ├── GUIDE.md                        #   交互流程、排盘调用、分析框架
│   │   ├── scripts/
│   │   │   ├── pai_pan.py                  #   四柱/大运排盘（标准库，无 pip 依赖）
│   │   │   └── test_pai_pan.py             #   排盘回归测试
│   │   └── references/                     #   五行/时辰/大运/神煞/典籍参考表
│   └── celizi/                             # 测字（拆字）
│       ├── GUIDE.md                        #   交互流程、分析框架
│       └── references/
│           └── chaizi-fa.md                #   八种拆字技法、偏旁引申联想表
├── LICENSE
└── README.md
```

## 免责声明

本 Skill 仅供传统文化学习与娱乐参考，分析结果不构成任何决策依据。命理学属于传统文化范畴，请理性看待。
