![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)
![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)
![Tests](https://github.com/WENSHAO521/bazi-skill/actions/workflows/tests.yml/badge.svg)

# 赛博算命 Skill

基于 Claude Code 的综合命理分析工具。通过交互式对话收集信息，参照传统典籍进行专业分析。支持**八字（四柱）**、**紫薇斗数**、**六爻（摇卦/纳甲）**、**奇门遁甲（时家）**、**姓名学（五格剖象）**、**测字（拆字）**六种方法。

## 功能

- **统一入口** — 一个 skill 覆盖六种命理方法，未指明方法时会先询问用户想用哪一种
- **八字（四柱）** — 逐步收集姓名、阳历/农历生日、出生时辰、性别、出生地等信息，自动排出年柱、月柱、日柱、时柱，计算大运与流年，结合九本经典典籍进行日主强弱、十神关系、五行平衡、格局判定、大运流年解读及综合建议
- **紫薇斗数** — 根据农历生日时辰排出命宫身宫、五行局、十二宫十四主星及四化，逐宫解读格局
- **六爻（摇卦/纳甲）** — 针对具体所问之事，用报数或摇钱法起卦，按京房纳甲装卦、定六亲世应、分析动爻变化
- **奇门遁甲（时家）** — 九宫飞盘、天盘地盘、八门九星八神排布分析；排局（阴阳遁/局数）因历史上存在多个互不相同的流派，暂需用户自行从黄历或专业工具查到后输入，本方法只负责排局之后的确定性布局计算，避免给出看似精确实则选错流派的结果
- **姓名学（五格剖象）** — 根据姓名各字的康熙繁体笔画数，计算天格/人格/地格/外格/总格及三才配置，对照 81 数吉凶表解读
- **测字（拆字）** — 只需一个汉字和想问的事情，结合传统拆字技法（增笔、减笔、拆字、会意、象形、谐音、假借、参形）做趣味解读

## 安装

> **注意**：Claude Code 从 git 仓库根目录的 `.claude/skills/` 查找 skill，请在正确的位置执行。八字、紫薇斗数、六爻、奇门遁甲、姓名学方法需要本机安装 `python3`（只用标准库，无额外 pip 依赖）；测字方法无额外依赖。

```bash
# 安装到当前项目（在 git 仓库根目录执行）
mkdir -p .claude/skills
git clone https://github.com/jinchenma94/bazi-skill .claude/skills/mingli

# 或安装到全局（所有项目都能用）
git clone https://github.com/jinchenma94/bazi-skill ~/.claude/skills/mingli
```

## 使用

在 Claude Code 中输入以下任意关键词即可触发：

`算命` `命理` `占卜` `算八字` `看八字` `批八字` `排八字` `四柱` `命盘` `排盘` `bazi`
`紫薇斗数` `紫微斗数` `六爻` `摇卦` `起卦` `奇门遁甲` `起局` `姓名学` `五格剖象` `测字` `拆字` `相字`

如果只是笼统地说"算命"、"看看运势"，skill 会先询问你想用哪种方法。若明确说出了方法（如"帮我摇一卦"），会直接进入对应流程。

各方法确认信息后会执行对应排盘/起卦脚本（依赖本机 **python3** 3.6+，只用标准库），例如：

```bash
python3 methods/bazi/scripts/pai_pan.py --solar 1990-05-15 --shichen 午 --sex 男
python3 methods/ziwei/scripts/pai_pan_ziwei.py --lunar 1990-04-21 --shichen 午 --sex 男
python3 methods/liuyao/scripts/qigua.py --numbers 3 5 7
python3 methods/qimen/scripts/paiju.py --yangdun --ju 1 --solar 1990-05-15 --hour 12:00
python3 methods/xingming/scripts/wuge.py --surname 7 --given 4 8
```

测字流程不需要脚本计算，只需一个汉字和想问的事情即可开始。

## 参考典籍与资料来源

| 方法 | 主要参考 |
|------|----------|
| 八字 | 《穷通宝典》《三命通会》《滴天髓》《渊海子平》《千里命稿》《协纪辨方书》《果老星宗》《子平真诠》《神峰通考》 |
| 紫薇斗数 | 传统安星诀，`methods/ziwei/references/anxing-guize.md` 标注了各条规则的置信度和已知流派分歧 |
| 六爻 | 京房纳甲、八宫卦变，`methods/liuyao/references/najia-guize.md` |
| 奇门遁甲 | 排局部分因流派分歧交由用户提供，布局部分见 `methods/qimen/references/paiju-guize.md`（含置信度标注） |
| 姓名学 | 熊崎氏姓名学五格剖象法、81 数吉凶通行版本，`methods/xingming/references/` |
| 测字 | 《测字秘牒》《相字心易补遗》一类民间典籍记载的拆字技法，`methods/celizi/references/chaizi-fa.md` |

## 项目结构

```
bazi-skill/
├── SKILL.md                                # Skill 入口（路由：确定用户想用哪种方法）
├── methods/
│   ├── bazi/                               # 八字（四柱）
│   │   ├── GUIDE.md
│   │   ├── scripts/{pai_pan.py, test_pai_pan.py}
│   │   └── references/                     #   五行/时辰/大运/神煞/典籍参考表
│   ├── ziwei/                              # 紫薇斗数
│   │   ├── GUIDE.md
│   │   ├── scripts/{pai_pan_ziwei.py, test_pai_pan_ziwei.py}
│   │   └── references/{anxing-guize.md, xingyao-jieyi.md}
│   ├── liuyao/                             # 六爻（摇卦/纳甲）
│   │   ├── GUIDE.md
│   │   ├── scripts/{qigua.py, test_qigua.py}
│   │   └── references/{najia-guize.md, liuqin-yongshen.md}
│   ├── qimen/                              # 奇门遁甲（时家）
│   │   ├── GUIDE.md
│   │   ├── scripts/{paiju.py, test_paiju.py}
│   │   └── references/{paiju-guize.md, gong-men-xing-shen-jieyi.md}
│   ├── xingming/                           # 姓名学（五格剖象）
│   │   ├── GUIDE.md
│   │   ├── scripts/{wuge.py, test_wuge.py}
│   │   └── references/{wuge-suanfa.md, 81-shuli.md}
│   └── celizi/                             # 测字（拆字）
│       ├── GUIDE.md
│       └── references/chaizi-fa.md
├── LICENSE
└── README.md
```

## 已知限制

- **奇门遁甲的排局**（阴遁/阳遁、局数）暂不支持全自动计算：这一步依赖的"置闰法"历史上有拆补法、置闰法、茅山法等多个并行流派，同一时刻可能算出不同局数，属于命理学界公开承认的分歧，而非计算错误。为避免给出一个看似精确实则选错流派的结果，本方法要求用户自行从黄历、万年历 App 或专业奇门软件查到局数后输入，脚本只负责局数确定之后的九宫布局计算。
- **紫薇斗数的闰月归属**、**姓名学部分数理的吉凶等级**等环节存在流派差异，已在对应 references 文件中标注置信度，解读时会如实体现不确定性，不作绝对化断言。

## 免责声明

本 Skill 仅供传统文化学习与娱乐参考，分析结果不构成任何决策依据。命理学属于传统文化范畴，请理性看待。
