# daily-arXiv 完整使用与修改指南

> 从环境搭建到代码修改，一份文档讲清楚这个项目怎么用、怎么改。

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 环境依赖与搭建](#2-环境依赖与搭建)
- [3. 仓库结构详解](#3-仓库结构详解)
- [4. 核心算法原理](#4-核心算法原理)
- [5. 完整数据流](#5-完整数据流)
- [6. 修改指南：收窄到具身智能](#6-修改指南收窄到具身智能)

---

## 1. 项目概述

这是一个**全自动 arXiv 论文追踪 + AI 增强系统**。每天定时从 arXiv 抓取指定领域的最新论文，通过 LLM 自动生成结构化的 TL;DR、动机、方法、结果、结论，最终部署为带密码保护的 GitHub Pages 网站供浏览。

**核心能力：**
- 自动爬取 arXiv 每日新论文
- 7 天滑动窗口去重
- LLM 结构化摘要增强（TL;DR + Motivation + Method + Result + Conclusion）
- Markdown 格式输出
- 密码保护的 Web 前端（分类导航、关键词/作者过滤、文本搜索、统计可视化）

**当前覆盖领域：** `cs.CV`（计算机视觉）、`cs.CL`（计算语言学）

---

## 2. 环境依赖与搭建

### 2.1 技术栈

| 层次 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| 包管理 | `uv`（由 astral.sh 提供） |
| 爬虫框架 | Scrapy 2.12+ |
| arXiv API | `arxiv` 库 (>=2.1.3) |
| LLM 集成 | LangChain + langchain-openai |
| 前端 | 纯 HTML/CSS/JS（GitHub Pages） |
| CI/CD | GitHub Actions |
| 前端依赖 | D3.js（统计图）、compromise.js（NLP 关键词提取） |

### 2.2 本地环境搭建

```bash
# 1. 安装 uv（Python 包管理器）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装项目依赖
uv sync

# 3. 设置必需的环境变量
export OPENAI_API_KEY="your-api-key-here"          # 必需：LLM API Key
export OPENAI_BASE_URL="https://api.openai.com/v1" # 可选：API 代理地址
export LANGUAGE="Chinese"                          # 输出语言
export CATEGORIES="cs.CV, cs.CL"                   # 关注的 arXiv 分类
export MODEL_NAME="deepseek-chat"                  # 使用的 LLM 模型
export TOKEN_GITHUB="ghp_xxx"                      # 可选：GitHub 代码链接检测
```

### 2.3 项目依赖 (`pyproject.toml`)

```
dependencies = [
    arxiv>=2.1.3,            # arXiv API 封装
    dotenv>=0.9.9,           # 环境变量加载
    langchain>=0.3.20,       # LLM 编排框架
    langchain-openai>=0.3.9, # OpenAI 兼容 LLM 适配器
    scrapy>=2.12.0,          # 爬虫框架
    tqdm>=4.67.1,            # 进度条
]
```

### 2.4 本地运行

```bash
# 完整流程（需要 OPENAI_API_KEY）
bash run.sh

# 或分步执行：
cd daily_arxiv
scrapy crawl arxiv -o ../data/2026-07-06.jsonl    # 仅爬取
cd ../ai
python enhance.py --data ../data/2026-07-06.jsonl  # AI 增强
cd ../to_md
python convert.py --data ../data/2026-07-06_AI_enhanced_Chinese.jsonl  # 转 Markdown
```

**run.sh 的 5 个步骤：**

```
Step 1: scrapy crawl arxiv        → data/{日期}.jsonl
Step 2: check_stats.py            → 去重检查（7 天窗口）
Step 3: ai/enhance.py             → data/{日期}_AI_enhanced_{语言}.jsonl
Step 4: to_md/convert.py          → data/{日期}.md
Step 5: 更新 assets/file-list.txt
```

---

## 3. 仓库结构详解

```
daily-arXiv/
├── .github/workflows/run.yml          # ★ CI/CD 核心：定时触发整个流水线
├── daily_arxiv/                       # ★ Scrapy 爬虫项目
│   ├── config.yaml                    # 配置文件：分类列表 + 模型名
│   ├── scrapy.cfg                     # Scrapy 部署配置
│   └── daily_arxiv/
│       ├── spiders/arxiv.py           # ★ 爬虫核心：页面抓取 + 分类过滤
│       ├── pipelines.py               # ★ Pipeline：arxiv API 获取完整元数据
│       ├── items.py                   # Item 定义（仅 id 字段）
│       ├── settings.py                # Scrapy 设置
│       ├── middlewares.py             # 中间件
│       └── check_stats.py             # ★ 去重脚本：7 天滑动窗口
├── ai/                                # ★ AI 增强模块
│   ├── enhance.py                     # ★ 主入口：LLM 并行处理管线
│   ├── structure.py                   # Pydantic Schema（TL;DR 等 5 字段）
│   ├── system.txt                     # LLM System Prompt
│   └── template.txt                   # LLM User Prompt 模板
├── to_md/                             # ★ Markdown 转换模块
│   ├── convert.py                     # JSONL → 分组 Markdown
│   └── paper_template.md              # 单篇论文渲染模板
├── data/                              # ★ 运行时数据（JSONL + MD）
├── assets/                            # 静态资源（图片、视频）
├── js/                                # 前端 JS
│   ├── app.js                         # 核心交互（论文加载/过滤/搜索）
│   ├── settings.js                    # 设置页（关键词/作者偏好）
│   ├── statistic.js                   # 统计页（D3 关键词云 + 趋势图）
│   ├── auth.js + auth-config.js       # 密码认证
│   └── data-config.js                 # CI 注入仓库信息
├── css/                               # 样式
├── index.html / login.html / settings.html / statistic.html  # 前端页面
├── SKILL/                             # SKILL 定义（外部调用接口）
├── run.sh                             # 本地调试一键脚本
├── pyproject.toml                     # 项目元数据 + 依赖
└── uv.lock                            # 依赖锁定文件
```

### 各模块职责总结

| 模块 | 文件 | 职责 |
|------|------|------|
| **爬虫** | `arxiv.py` | 访问 `arxiv.org/list/{cat}/new`，解析论文 ID + 分类 |
| **充实** | `pipelines.py` | 用 arxiv API 根据 ID 获取标题、作者、摘要等完整信息 |
| **去重** | `check_stats.py` | 对比过去 7 天数据，移除重复论文 |
| **增强** | `enhance.py` | 并行调用 LLM，为每篇论文生成结构化分析 |
| **转换** | `convert.py` | 按分类分组，生成 Markdown |
| **前端** | `js/app.js` | 加载 JSON 数据，提供分类/关键词/作者/文本过滤 |
| **调度** | `run.yml` | GitHub Actions 每天 UTC 1:30 自动执行完整流程 |

---

## 4. 核心算法原理

### 4.1 论文抓取流程

```
                          ┌─────────────────────┐
                          │  GitHub Actions 定时  │
                          │  每天 UTC 1:30 触发   │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  Scrapy Spider       │
                          │  读取 CATEGORIES     │
                          │  环境变量（如 cs.CV） │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
             arxiv.org        arxiv.org         arxiv.org
           /list/cs.CV/new  /list/cs.CL/new  /list/cs.RO/new
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  解析每篇论文的        │
                          │  list-subjects 分类   │
                          │  与目标分类取交集      │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  arxiv API (pipeline) │
                          │  获取完整元数据        │
                          │  - title, authors     │
                          │  - categories, summary│
                          │  - comment (已发表信息) │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  check_stats.py      │
                          │  7 天滑动窗口去重     │
                          │  对比过去 7 天的 ID   │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  输出: {日期}.jsonl   │
                          └─────────────────────┘
```

### 4.2 爬虫详解 (`arxiv.py`)

```
Spider 初始化：
  1. 从环境变量 CATEGORIES 读取目标分类列表（如 "cs.CV, cs.CL"）
  2. 构造 start_urls: ["arxiv.org/list/cs.CV/new", "arxiv.org/list/cs.CL/new"]
  3. 将分类转为集合 self.target_categories 用于后续交集判断

解析过程 (parse 方法)：
  1. 提取页面上所有 "item" 锚点序号，跳过公告区（大序号锚点）
  2. 遍历每篇论文的 <dt> + <dd> 对：
     - 从 <a title='Abstract'> 提取 arxiv_id（如 "2501.12345v1"）
     - 从 .list-subjects 提取分类代码（正则匹配括号内内容）
     - 用 paper_categories ∩ target_categories 判断是否保留
  3. 只 yield 分类匹配的论文
```

### 4.3 Pipeline 详解 (`pipelines.py`)

```
对每篇从 Spider 获取的论文：
  1. 构造 abs URL 和 pdf URL
  2. 调用 arxiv.Search(id_list=[arxiv_id]) 
  3. 通过 arxiv 官方 API 获取完整元数据
  4. 补充字段：title, authors, categories, comment, summary
  5. 返回完整的 item dict
```

### 4.4 去重算法 (`check_stats.py`)

```
算法：7 天滑动窗口去重
  1. 加载今日数据 all_papers
  2. 对过去 7 天 (i=1~7)：
     - 加载 date_i.jsonl
     - 提取其中的论文 ID，加入 history_ids 集合
  3. 计算 duplicate_ids = today_ids ∩ history_ids
  4. 从今日数据中移除重复项
  5. 如果全部重复：删除今日文件，exit(1)
  6. 如果有新内容：保存去重后的文件，exit(0)
```

### 4.5 AI 增强详解 (`enhance.py`)

```
完整管线：
  1. 读取 JSONL 数据
  2. 内存去重（按 id）
  3. 对每篇论文并行处理（ThreadPoolExecutor）：
     a. 敏感内容检测 → 调用 spam.dw-dengwei.workers.dev API
     b. GitHub 代码链接提取 → 正则匹配 + GitHub API 获取 stars
     c. LLM 结构化增强 → 输入 abstract，输出 5 个字段
     d. AI 输出敏感词检测 → 再次检查生成内容
  4. 输出 {日期}_AI_enhanced_{语言}.jsonl

LLM 调用细节：
  - 使用 LangChain ChatOpenAI + with_structured_output(Structure)
  - Structure 模型定义（Pydantic BaseModel）：
    { tldr, motivation, method, result, conclusion }
  - 错误处理：JSON 解析失败 → 提取部分字段 + 默认值兜底
  - 支持自定义 model_name 和 base_url（通过环境变量）
```

### 4.6 LLM Prompt 设计

**System Prompt (`ai/system.txt`)：**
```
You are a professional paper analyst.
- 要求简洁、详细、准确，使用正确术语
- 禁止输出政治、民族、宗教等敏感内容
- 输出语言：{language}（由环境变量控制，默认 Chinese）
```

**User Prompt (`ai/template.txt`)：**
```
Please analyze the following abstract of papers.
Content:
{content}
```

### 4.7 结构化输出 Schema (`ai/structure.py`)

| 字段 | 含义 | 要求 |
|------|------|------|
| `tldr` | 一句话总结 | 论文核心贡献的高度概括 |
| `motivation` | 研究动机 | 为什么要做这个工作 |
| `method` | 方法 | 核心方法描述 |
| `result` | 实验结果 | 关键实验结果和发现 |
| `conclusion` | 结论 | 研究结论和意义 |

### 4.8 Markdown 转换 (`to_md/convert.py`)

```
流程：
  1. 读取 AI 增强后的 JSONL
  2. 按论文的第一分类分组
  3. 按 CATEGORIES 环境变量中的顺序排序分类
  4. 生成 Table of Contents（带论文计数）
  5. 每分类生成一个 section
  6. 对每篇论文，用 paper_template.md 模板填充：
     - 标题、作者、分类、链接
     - TL;DR（始终可见）
     - <details> 折叠区：Motivation / Method / Result / Conclusion / Abstract
  7. 输出 {日期}.md
```

---

## 5. 完整数据流

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Step 1      │    │  Step 2      │    │  Step 3      │    │  Step 4      │
│  爬取        │───▶│  去重        │───▶│  AI 增强     │───▶│  Markdown    │
│  arxiv.py    │    │  check_stats │    │  enhance.py  │    │  convert.py  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  yyyy-mm-dd          去重后的             AI增强后的          yyyy-mm-dd
  .jsonl              同日文件            同日文件             .md
  (仅ID+分类)                            (完整+AI字段)       (网页展示用)

                              GitHub Actions
                         ┌──────────────────┐
                         │ main 分支：代码    │ → GitHub Pages（网站前端）
                         │ data 分支：数据    │ → 论文 JSONL + MD 文件
                         └──────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  前端数据加载层                                              │
  │  js/data-config.js → 指向 GitHub Pages raw URL              │
  │  js/app.js         → 获取 JSONL → 解析 → 渲染               │
  │                                                             │
  │  前端过滤层（纯客户端）：                                     │
  │  - 分类过滤    (从数据中解析 category)                       │
  │  - 关键词过滤  (localStorage 存储，匹配 title + abstract)     │
  │  - 作者过滤    (localStorage 存储，匹配 authors)             │
  │  - 文本搜索    (实时输入匹配)                                 │
  │  - 日期选择    (assets/file-list.txt 中的文件列表)           │
  └─────────────────────────────────────────────────────────────┘
```

### 双分支策略

| 分支 | 内容 | 用途 |
|------|------|------|
| `main` | 代码（Python + HTML/JS/CSS） | GitHub Pages 部署 |
| `data` | 数据文件（JSONL + MD） | 前端通过 raw URL 拉取论文数据 |

---

## 6. 修改指南：收窄到具身智能

> **目标：** 将每日论文推荐范围从泛计算机视觉/语言，收窄到具身智能（Embodied AI），覆盖 VLA、VLN、VLX、WM、WAM、RL 等相关方向。

### 6.1 核心思路

arXiv 目前**没有**专门的 "Embodied AI" 分类。相关论文分散在以下分类中：

| arXiv 分类 | 含义 | 与具身智能的关系 |
|------------|------|-----------------|
| `cs.RO` | 机器人学 (Robotics) | **核心分类**，VLA/VLN 等主阵地 |
| `cs.CV` | 计算机视觉 | 3D 视觉、场景理解、视频模型 |
| `cs.AI` | 人工智能 | 通用 AI 方法 |
| `cs.LG` | 机器学习 | RL、IL、表征学习 |
| `cs.CL` | 计算语言学 | 多模态、指令跟随、VLM |
| `cs.MA` | 多智能体系统 | 多机器人协作 |
| `cs.HC` | 人机交互 | 人机协作、可教机器人 |

**方案：扩大分类范围 + 关键词二次过滤**

因为仅靠 arXiv 分类无法精确命中具身智能论文，核心策略是：
1. 扩大爬取范围到 6-7 个相关分类
2. 在 Pipeline 或后续步骤中按关键词过滤
3. 可选：在 AI 增强的 Prompt 中加入领域定制

### 6.2 具体修改步骤

#### 第一步：修改分类配置

**文件 `daily_arxiv/config.yaml`：**

```yaml
arxiv:
  categories:
    - cs.RO
    - cs.CV
    - cs.AI
    - cs.LG
    - cs.CL
    - cs.MA

llm:
  model_name: 'deepseek-chat'
```

**文件 `.github/workflows/run.yml`（只改一处）：**

找到 `CATEGORIES` 的声明行（大约在第 45 行），改为：
```yaml
export CATEGORIES="cs.RO, cs.CV, cs.AI, cs.LG, cs.CL, cs.MA"
```

**文件 `run.sh`（本地调试）：**

找到默认值行（大约在第 45 行），改为：
```bash
export CATEGORIES="${CATEGORIES:-cs.RO, cs.CV, cs.AI, cs.LG, cs.CL, cs.MA}"
```

#### 第二步：添加关键词过滤 Pipeline

这是**核心修改**。在 `daily_arxiv/daily_arxiv/pipelines.py` 中添加具身智能关键词过滤器。

修改后的 `pipelines.py`：

```python
import arxiv
import json
import os
import sys
import re
from datetime import datetime, timedelta


# ★ 具身智能关键词配置（可根据需要增删）
EMBODIED_AI_KEYWORDS = [
    # VLA (Vision-Language-Action)
    "vision-language-action", "vision language action", "VLA",
    "robot manipulation", "robot control policy", "visuomotor",
    "action policy", "robot policy", "behavior cloning",

    # VLN (Vision-and-Language Navigation)
    "vision-and-language navigation", "vision language navigation", "VLN",
    "visual navigation", "waypoint", "instruction following navigation",

    # VLX (Vision-Language-X)
    "vision-language model.*robot", "vision language model.*action",
    "multimodal.*embodied", "embodied.*multimodal", "grounded VLM",

    # World Model / WAM / WM
    "world model", "world action model", "WAM",
    "model-based RL.*robotics", "learned dynamics.*robot",
    "diffusion policy", "video prediction.*robot",

    # RL (Reinforcement Learning) in Robotics
    "reinforcement learning.*robot", "reinforcement learning.*manipulation",
    "reinforcement learning.*grasping", "RL.*robotics",
    "sim-to-real", "sim to real", "domain randomization.*robot",
    "reward function.*robot", "reward.*manipulation",
    "PPO.*robot", "SAC.*robot", "DQN.*robot",

    # Imitation Learning
    "imitation learning.*robot", "learning from demonstration",
    "demonstration learning", "IL.*robotics", "action chunking",

    # Embodied / Spatial AI
    "embodied AI", "embodied agent", "embodied.*navigation",
    "embodied.*interaction", "spatial AI", "spatial reasoning.*robot",
    "3D scene understanding.*robot",

    # Dexterous Manipulation
    "dexterous manipulation", "robot grasping", "bimanual",
    "dual-arm", "tactile.*robot", "contact-rich",

    # Mobile Manipulation / Locomotion
    "mobile manipulation", "legged locomotion",
    "quadruped", "bipedal", "humanoid.*robot",

    # LLM/VLM for Robotics  
    "large language model.*robot", "LLM.*robotics",
    "foundation model.*robot", "foundation model.*embodied",
    "VLM.*robot", "VLM.*manipulation",

    # Task Planning
    "task and motion planning", "task planning.*robot",
    "hierarchical RL.*robot", "skill chaining",
]


def matches_embodied_ai(title: str, summary: str) -> bool:
    """
    检查论文标题和摘要是否匹配具身智能关键词。
    大小写不敏感，至少匹配一个关键词即视为相关。
    """
    combined = (title + " " + summary).lower()

    for kw in EMBODIED_AI_KEYWORDS:
        if re.search(kw.lower(), combined):
            return True
    return False


class DailyArxivPipeline:
    def __init__(self):
        self.page_size = 100
        self.client = arxiv.Client(self.page_size)
        # 可通过环境变量控制是否启用关键词过滤
        self.enable_filter = os.environ.get("ENABLE_KEYWORD_FILTER", "true").lower() == "true"

    def process_item(self, item: dict, spider):
        item["pdf"] = f"https://arxiv.org/pdf/{item['id']}"
        item["abs"] = f"https://arxiv.org/abs/{item['id']}"
        search = arxiv.Search(
            id_list=[item["id"]],
        )
        paper = next(self.client.results(search))
        item["authors"] = [a.name for a in paper.authors]
        item["title"] = paper.title
        item["categories"] = paper.categories
        item["comment"] = paper.comment
        item["summary"] = paper.summary

        # ★ 具身智能关键词过滤
        if self.enable_filter:
            title = item.get("title", "")
            summary = item.get("summary", "")
            if not matches_embodied_ai(title, summary):
                spider.logger.info(
                    f"Skipped (not embodied AI) {item['id']}: {title[:80]}..."
                )
                from scrapy.exceptions import DropItem
                raise DropItem(f"Not embodied AI related: {item['id']}")

        return item
```

#### 第三步：修改 AI Prompt（可选但推荐）

在 `ai/system.txt` 中加入具身智能领域知识，让 LLM 用领域术语分析论文：

```txt
You are a professional paper analyst specializing in Embodied AI and Robotics.
Your expertise covers: Vision-Language-Action (VLA) models, Vision-and-Language
Navigation (VLN), world models for robotics, reinforcement learning for 
manipulation, robot foundation models, imitation learning, dexterous 
manipulation, and sim-to-real transfer.

You should avoid unnecessarily long replies and instead provide concise, 
detailed, and precise answers using correct terminology.
When analyzing papers, highlight connections to embodied AI, robot learning,
and related subfields.

It is prohibited to output any sensitive content such as politics, ethnicity,
religion, violence, pornography, terrorism, gambling, regional discrimination,
leaders and their relatives; once it is detected that the question or original
text contains the above elements, the unified reply will be: 
"This content has not passed the compliance test and has been hidden."

Your output should in {language}.
```

### 6.3 修改总结

| 序号 | 文件 | 修改内容 | 必要性 |
|------|------|----------|--------|
| 1 | `daily_arxiv/config.yaml` | 分类改为 cs.RO, cs.CV, cs.AI, cs.LG, cs.CL, cs.MA | **必须** |
| 2 | `.github/workflows/run.yml` | 同上，更新 CATEGORIES 环境变量 | **必须** |
| 3 | `run.sh` | 同上，更新默认 CATEGORIES 值 | 推荐 |
| 4 | `daily_arxiv/daily_arxiv/pipelines.py` | 添加 `matches_embodied_ai()` + DropItem 逻辑 | **必须** |
| 5 | `ai/system.txt` | 加入具身智能领域描述 | 推荐 |

### 6.4 关键设计决策：为什么在 Pipeline 而非 Spider 中过滤？

| 位置 | 可行？ | 优劣 |
|------|--------|------|
| Spider (`arxiv.py`) | 不可行 | Spider 阶段只有 arxiv_id 和页面上的分类信息，**没有标题和摘要**，无法做关键词匹配 |
| Pipeline (`pipelines.py`) | **推荐** | 此时已通过 arxiv API 获取完整元数据（title + summary），可以执行关键词过滤 |
| 后处理 (`enhance.py`) | 可行 | 但此时已经白爬了不相关论文，浪费 API 带宽和 LLM token |

使用 `DropItem` 异常丢弃不符合关键词的论文，Scrapy 会自动跳过这些 item，不会写入输出文件。

### 6.5 测试验证

```bash
# 1. 设置环境变量
export CATEGORIES="cs.RO, cs.CV, cs.AI, cs.LG"
export ENABLE_KEYWORD_FILTER="true"

# 2. 只爬取测试（不触发 AI）
cd daily_arxiv
scrapy crawl arxiv -o ../data/test.jsonl

# 3. 检查输出：确认每篇论文确实与具身智能相关
cat ../data/test.jsonl | python -m json.tool | grep -i "title\|summary"

# 4. 统计数量
wc -l ../data/test.jsonl
```

### 6.6 可选增强

**自定义关键词列表：** 可以通过环境变量 `KEYWORD_CONFIG` 指向自定义关键词 JSON 文件，避免硬编码：

```python
# 在 pipelines.py 中添加
keyword_file = os.environ.get("KEYWORD_CONFIG", "")
if keyword_file and os.path.exists(keyword_file):
    with open(keyword_file) as f:
        EMBODIED_AI_KEYWORDS = json.load(f)
```

**Prometheus 友好的关键词结构：**

```json
{
  "must_have": ["robot", "embodied", "manipulation", "navigation"],
  "should_have": ["reinforcement learning", "imitation learning", "VLA", "world model"],
  "enhance_score": ["dexterous", "bimanual", "sim-to-real"]
}
```

可按匹配类型打分：`must_have` 命中 1 个方可入选（AND），`should_have` 用于排序加权。

---

## 附录：关键参考

- arXiv 分类列表：https://arxiv.org/category_taxonomy
- Scrapy DropItem 文档：https://docs.scrapy.org/en/latest/topics/exceptions.html#dropping-items
- 项目原有 README：[README.md](README.md)
- GitHub Actions 定时语法：`cron: "30 1 * * *"` = 每天 UTC 1:30（北京时间 9:30）
