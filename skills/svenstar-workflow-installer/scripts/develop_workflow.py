#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import date
from pathlib import Path


WORKFLOW_CUSTOM_START = "<!-- SVENSTAR_WORKFLOW_CUSTOM_START -->"
WORKFLOW_CUSTOM_END = "<!-- SVENSTAR_WORKFLOW_CUSTOM_END -->"
AGENTS_START = "<!-- SVENSTAR_DEVELOP_WORKFLOW_START -->"
AGENTS_END = "<!-- SVENSTAR_DEVELOP_WORKFLOW_END -->"


WORKFLOW_MD = f"""# Task 工作流

本文件定义两套协作模式。默认使用轻量模式；只有长任务才启用 `docs/develops/` 目录和任务状态机，完成后一定要 git 提交。

## 模式选择

默认使用轻量模式。

只有满足以下任一条件时，才进入长任务模式：

- 用户明确要求按 `WORKFLOW.md`、`task.json`、拆任务或长期工作流执行。
- 需求预计跨多个会话。
- 需求需要 3 个以上可独立验证任务。
- 需求跨前端、后端、API 契约、数据库或架构文档。
- 当前改动需要长期上下文交接。

如果用户没有明确要求长任务模式，但 agent 判断复杂度超过上述阈值，必须先询问用户是否进入长任务模式；不要自动创建 `docs/develops/<需求目录>/`。

## 需求分析与 PRD 候选

当用户要求先讨论、grill、brainstorming 或设计一个需求，但尚未明确要求开始开发时：

- 可以先把确认后的需求分析 / 设计 / PRD 候选写到 `docs/superpowers/YYYY-MM-DD-<topic>-design.md`，内容尽量使用中文。
- `docs/superpowers/` 只承载尚未进入开发工作流的候选规格，不维护任务状态、进度或验收日志。
- 不因为写了 `docs/superpowers/` 文档就自动进入长任务模式，也不要自动创建 `docs/develops/<需求目录>/`。
- 用户明确指定“开发这个需求”、要求按 `WORKFLOW.md` 执行，或确认进入长任务模式后，将对应候选规格移动到 `docs/develops/<需求目录>/prd.md`，作为该需求的 PRD / 设计依据。
- 移动后，`docs/develops/<需求目录>/task.json` 承载任务状态，`current.md` 承载轻量接手上下文；不要继续在 `docs/superpowers/` 维护该需求的进度。

## 轻量模式

适用于明确的小修小改，例如修一个 bug、改一处 UI、调整一段小逻辑、补一个小测试。

轻量模式规则：

- 不创建 `docs/develops/<需求目录>/`。
- 不维护 `task.json`、`current.md`。
- 不写开发日志；需要记录时依赖 git diff、测试输出和 commit message。
- 仍需读取必要的稳定文档和相关代码，不做无上下文修改。
- 改行为时优先补测试或更新测试。
- 完成后运行最小必要验证；无法运行时说明原因。

## 长任务模式

长任务模式使用 `docs/develops/current.json` 指向唯一活跃目录。这个目录可以是需求根目录，也可以是某个阶段子目录。

新会话进入长任务模式时：

1. 读取稳定文档：`memory-bank/product.md`、`memory-bank/tech-stack.md`、`memory-bank/api-contract.md`、`memory-bank/architecture.md`。
2. 读取 `docs/develops/current.json`。
3. 进入 `docs/develops/<active>/`。
4. 只读取该目录下的 `task.json` 和 `current.md`。
5. 不读取其他 `docs/develops/` 历史目录，除非用户明确要求追溯；追溯时按日期、需求 slug、任务 id 或关键词局部搜索。

`docs/develops/current.json` 示例：

```json
{{
  "active": "2026-06-03-altcoin-momentum/p3-hypotheses",
  "updated_at": "2026-06-03",
  "status": "in_progress"
}}
```

没有活跃长任务时：

```json
{{
  "active": null,
  "updated_at": "2026-06-03",
  "status": "idle"
}}
```

## 长任务目录结构

每个大需求使用一个根目录；需要拆阶段时，阶段目录直接挂在根目录下：

```text
docs/develops/
  current.json
  _template/
    task.json
    current.md
  task.schema.json
  YYYY-MM-DD-feature-slug/
    prd.md
    task.json
    current.md
    phase-slug/
      task.json
      current.md
```

文件职责：

- `docs/develops/current.json`：唯一活跃目录指针。`active` 可以直接指向需求根目录，也可以指向 `<阶段>/` 子目录。
- `docs/develops/<需求>/prd.md`：该需求的 PRD / 设计依据；若该需求从 `docs/superpowers/` 的候选规格进入开发，应由对应候选规格移动而来。
- `docs/develops/<需求>/task.json`：需求根目录级任务状态机。适合记录跨阶段任务，或不拆阶段时直接使用。
- `docs/develops/<需求>/current.md`：需求根目录级轻量 handoff。适合记录大需求的总目标、当前阶段入口或跨阶段约束。
- `docs/develops/<需求>/<阶段>/task.json`：该阶段自己的任务状态机。阶段任务尽量留在阶段目录，不再为每个阶段新建平级需求目录。
- `docs/develops/<需求>/<阶段>/current.md`：该阶段自己的轻量 handoff。当前会话若聚焦某一阶段，`docs/develops/current.json` 应直接指向这里。
- `docs/develops/task.schema.json`：`docs/develops/**/task.json` 的结构约束。新增或批量调整任务时必须保持 JSON 可校验。
- `memory-bank/*.md`：稳定知识层。只放产品、技术栈、API 契约、架构和长期设计，不放开发流水账。

## Task 格式

`task.json` 只保留任务列表，避免重复写入工作流元数据：

```json
{{
  "tasks": [
    {{
      "id": "resource-list-query",
      "title": "补齐资源列表查询",
      "phase": "api-query",
      "description": "让 CLI 或 API 能查询核心资源列表。",
      "status": "todo",
      "depends_on": ["resource-schema"],
      "acceptance": [
        "CLI 或 API 可查询资源列表",
        "正常路径和空数据都有测试覆盖"
      ],
      "verification": [
        "cd backend && .venv/bin/python -m pytest tests/test_resource_query.py"
      ],
      "steps": [
        "扩展 query service 或 API service",
        "补齐入口参数",
        "补测试并运行验证"
      ],
      "notes": "改公开契约前先同步 memory-bank/api-contract.md",
      "evidence": []
    }}
  ]
}}
```

字段约定：

- `id`：稳定标识，可以是数字 id，也可以是语义化字符串；一旦创建不要重命名。
- `status`：唯一可信状态。允许值为 `todo`、`in_progress`、`blocked`、`review`、`done`。
- `depends_on`：前置任务 id。只在依赖已 `done` 时选择该任务。
- `acceptance`：人工可判断的验收条件，描述“什么算完成”。
- `verification`：必须执行或明确说明无法执行的验证命令、测试或检查。
- `steps`：建议执行步骤，不等同于验收条件；必要时可随实现细化，但不要删除原始意图。
- `notes`：短备注，只写约束、风险或不做什么。
- `evidence`：完成后记录关键验证证据，例如通过的测试命令或手动检查结果。

## 状态流

推荐状态流：

```text
todo -> in_progress -> review -> done
                  \\-> blocked
blocked -> todo | in_progress
review -> in_progress | done
```

状态含义：

- `todo`：尚未开始，或已重新放回待办。
- `in_progress`：当前会话正在实现或验证。
- `blocked`：被缺失信息、外部依赖、环境问题或设计冲突阻塞。必须写 `blocked_reason`。
- `review`：代码或文档已改完，但验收或验证还没有全部完成。
- `done`：所有 `acceptance` 满足，所有 `verification` 已通过或有明确、可接受的未运行说明，并已更新必要文档。

禁止事项：

- 禁止因为“代码写完了”直接标记 `done`。
- 禁止测试失败仍标记 `done`。
- 禁止用 `current.md` 里的描述覆盖 `task.json` 状态。
- 禁止把无关本地改动混进同一个 task 提交。

## 长任务执行流程

### 1. 初始化上下文

写代码前读取：

- `memory-bank/product.md`
- `memory-bank/tech-stack.md`
- `memory-bank/api-contract.md`
- `memory-bank/architecture.md`
- `docs/develops/current.json`
- `docs/develops/<active>/current.md`
- `docs/develops/<active>/task.json`

如果任务涉及 API 字段、响应格式、错误格式或公开行为，先更新 `memory-bank/api-contract.md`，再改实现和测试。

### 2. 选择任务

默认选择 1 个任务；只有强相关且能同一轮独立验证时才选择 2 个。

优先选择：

- `status=todo` 或可继续推进的 `status=review`。
- `depends_on` 全部为 `done`。
- 30 到 90 分钟内能形成可验证增量。
- 输入输出清晰，改动范围可控。
- 与当前代码上下文强相关。

避免选择：

- 前置依赖未完成的任务。
- 验收条件不清晰的任务。
- 改动范围横跨多个无关模块的任务。
- 高风险但缺少测试锚点的任务。

### 3. 测试先行与实现

默认采用测试先行：

- 改行为、修 bug、扩 API/client、调整后台任务、数据处理或核心业务流程时，优先先写测试或测试草案，再写实现。
- 新测试应先表达预期行为和边界条件；能跑出失败更好，但不要求为了形式主义制造红灯。
- 允许先实现再补测试的例外：纯文档任务、机械重命名、探索性 spike、测试锚点缺失且需要先定位边界、或用户明确要求快速原型。
- 使用例外时，必须在任务 `evidence` 或交接备注中说明原因和补上的验证方式。

实现要求：

- 遵循 `AGENTS.md` 和本仓库现有代码模式。
- 保持小改动，禁止顺手重构。
- 改行为时补测试或更新测试。

### 4. 验证

进入 `done` 前必须检查任务的每条 `acceptance` 和 `verification`。

验证结果记录到 `evidence`：

- 写明实际运行的命令和结果。
- 如果某个验证无法运行，写明原因、影响范围和替代检查。
- 若验证失败，任务保持 `in_progress` 或 `blocked`，不要标记 `done`。

### 5. 更新当前上下文

任务完成后：

- 将 `status` 改为 `done`。
- 更新 `evidence`。
- 更新 `docs/develops/<active>/current.md`，只保留当前焦点、卡点、下一步和少量接手备注。
- 若完成一个 phase、改变架构或形成长期决策，同步更新 `memory-bank/architecture.md` 或新增 ADR。
- 在标记 `done` 前检查本次需求是否影响使用或运维入口；如果影响命令、脚本、公开行为、调度方式、排障方式或架构边界，同步更新 `README.md`、相关 `memory-bank/*.md`、deployment/runbook 文档和示例命令。

任务未完成但需要交接时：

- 保持 `status=in_progress`、`review` 或 `blocked`。
- 在 `docs/develops/<active>/current.md` 写清当前焦点、卡点和下一步。
- 不要把完整开发过程写进 `current.md`。

### 6. 阶段切换与瘦身

当一个 phase 的全部任务进入 `done` 后：

- 如需进入下一阶段，在同一需求根目录下创建 `<next-phase>/`，并把 `docs/develops/current.json.active` 切到新阶段目录。
- 从当前活跃目录的 `task.json` 移除已经稳定完成且后续不会再改动的 `done` 任务，只保留接下来仍要推进的任务。
- `current.md` 只保留下一位 agent 接手必须知道的近期状态；不额外维护 append-only 开发日志。
- 跨阶段仍长期有效的结论，优先写入 `memory-bank/architecture.md`、相关设计文档，或下一阶段目录的 `current.md`。

### 7. 提交规则

轻量模式只有用户明确要求提交时才创建 commit。

长任务模式强制提交：

- 每个 task 进入 `done` 后必须创建 git commit。
- 阶段切换前如果已经形成可验证阶段性成果，也应在切换前完成一次 git commit。
- commit 只包含当前 task 或当前阶段相关文件。
- commit message 应包含等价的范围、任务、验证、决策和遗留摘要。
- 如果存在无关本地变更，禁止一并提交；先说明并只 stage 当前任务相关文件。
- 如果验证失败或任务未 `done`，禁止提交，除非用户明确要求保存 WIP。
- 不要 amend 旧提交，除非用户明确要求。

推荐 commit message 格式：

```text
<phase/task>: <一句话结果>

范围：...
任务：...
验证：...
决策：...
遗留：...
```

## Project Custom Notes

<!-- SVENSTAR_WORKFLOW_CUSTOM_START --><!-- SVENSTAR_WORKFLOW_CUSTOM_END -->
"""


TASK_SCHEMA = {
    "title": "Develop Workflow Task List",
    "type": "object",
    "additionalProperties": False,
    "required": ["tasks"],
    "properties": {
        "tasks": {
            "type": "array",
            "items": {"$ref": "#/$defs/task"},
        }
    },
    "$defs": {
        "task": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "title", "status", "acceptance", "verification"],
            "properties": {
                "id": {
                    "oneOf": [
                        {"type": "integer"},
                        {"type": "string", "minLength": 1},
                    ]
                },
                "title": {"type": "string", "minLength": 1},
                "phase": {"type": "string"},
                "description": {"type": "string"},
                "status": {"enum": ["todo", "in_progress", "blocked", "review", "done"]},
                "depends_on": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string", "minLength": 1},
                        ]
                    },
                    "uniqueItems": True,
                },
                "acceptance": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
                "verification": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
                "notes": {"type": "string"},
                "evidence": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
                "blocked_reason": {"type": "string"},
            },
        }
    },
}


TASK_TEMPLATE = {"tasks": []}


CURRENT_TEMPLATE = """# Current

## 当前焦点

- 当前任务：无。
- 当前状态：`idle`。
- 下一步：无。

## 卡点与约束

- 无。

## 轻量备注

- 本文件只保留当前需求或当前阶段的接手上下文，不写完整流水账。
- 完整验收条件、验证命令和证据以同目录 `task.json` 为准。
- 跨阶段长期有效的信息优先更新到稳定文档或下一阶段目录，不在这里维护 append-only 日志。
"""

SUPERPOWERS_README = """# Superpowers（候选需求与设计草案）

本目录放有价值但尚未进入开发工作流的需求分析、设计草案、PRD 候选和点子。它们不是当前事实，也不是历史归档，而是将来也许会做的备选方案，或刚完成讨论但尚未启动开发的候选规格。

## 规则

- 默认不读：AI 默认不读本目录，只有用户明确点名某份文档时才读。
- 不驱动开发：本目录内容不构成当前需求或契约；与 `memory-bank/` 冲突时以 `memory-bank/` 为准。
- 开发即移动：某个候选需求一旦决定按 `WORKFLOW.md` 进入开发，将对应文档移动到 `docs/develops/<需求目录>/prd.md`，再拆成可独立验证的 `task.json` 任务；稳定结论再固化进 `memory-bank/`。
- 不维护进度：本目录不维护任务状态、验收证据或开发日志。
- 尽量中文：新增需求分析、设计草案和 PRD 候选尽量使用中文；命令、路径、接口字段、事件名和状态值保留原文。

## 当前内容

暂无候选规格。已进入开发工作流的需求应查看 `docs/develops/`。
"""


MEMORY_BANK_FILES = {
    "README.md": """# Memory Bank

本目录保存项目当前事实源。AI 理解项目现状时应优先读取这里，而不是历史归档、候选需求或开发流水账。

## 默认可读

- `product.md`：当前产品定位、用户、使用场景和已实现能力。
- `tech-stack.md`：当前技术栈、运行入口、依赖管理和测试命令。
- `api-contract.md`：当前 API、数据结构、错误格式和前后端契约。
- `architecture.md`：当前架构、模块边界、依赖方向和关键实现事实。
- `deployment.md`：当前部署、运行、运维、排障和环境变量信息。

## 读取规则

- 默认不要读取 `docs/superpowers/` 或 `docs/archive/`。
- `docs/superpowers/` 只保存尚未进入开发工作流的候选需求、设计草案和点子。
- `docs/archive/` 只保存历史资料；历史资料不能覆盖本目录、当前代码或测试中的事实。
- 如果本目录与当前代码明显冲突，先判断哪一边过时；修正事实源后再改实现。
""",
    "product.md": """# Product

## 产品定位

TODO：说明这个项目解决什么问题、面向哪些用户、哪些能力已经稳定存在。

## 目标用户

TODO：列出主要用户、使用场景和非目标用户。

## 主要使用场景

TODO：用稳定的项目语言描述 2-5 个核心工作流。

## 已实现能力

TODO：只记录已经存在并可验证的能力。候选需求和未来想法放到 `docs/superpowers/`。

## 非目标

TODO：记录明确不做的范围，避免后续需求误扩。
""",
    "tech-stack.md": """# Tech Stack

## Runtime

TODO：记录语言版本、包管理器、主要运行入口和本地开发方式。

## Backend

TODO：记录后端框架、数据库、任务队列、CLI、爬虫、外部服务等事实。

## Frontend

TODO：记录前端框架、构建工具、UI 库、状态管理和测试工具等事实。

## Common Commands

```bash
# TODO：安装依赖
# TODO：运行后端测试
# TODO：运行前端构建或测试
```

## Notes

TODO：记录依赖管理、脚本职责、环境变量和本地运行约束。
""",
    "api-contract.md": """# API Contract

## 基本约定

TODO：记录 API base path、认证方式、请求格式、错误格式、分页、时间和数值精度约定。

## 数据结构

TODO：记录前后端共享的核心类型。字段名、枚举值和可空性必须与代码一致。

## Endpoints

TODO：按 endpoint 记录 method、path、query/body、response 和错误情况。

## 变更规则

- 修改公开请求字段、响应字段、错误格式或语义前，先更新本文件。
- 同步更新后端实现、前端 client/types 和测试。
""",
    "architecture.md": """# Architecture

## Top Level

TODO：描述仓库顶层目录和职责边界。

## Module Boundaries

TODO：记录核心模块、依赖方向和禁止跨层调用的规则。

## Data Flow

TODO：描述主要数据流、状态流和关键持久化边界。

## Important Decisions

TODO：记录当前仍有效的架构决策。历史方案放到 `docs/archive/`。

## Operational Notes

TODO：记录影响运行、排障、数据迁移或兼容性的实现事实。
""",
    "deployment.md": """# Deployment

## Environments

TODO：记录本地、测试、生产等环境差异。

## Configuration

TODO：记录必需环境变量、配置文件位置和敏感信息处理方式。不要写真实 secret。

## Runbook

TODO：记录启动、停止、迁移、备份、恢复、健康检查和常见排障步骤。

## Scheduled Jobs

TODO：记录定时任务、后台任务和手动运维命令。
""",
}


AGENTS_BLOCK = f"""{AGENTS_START}
## Svenstar Workflow Installer

- 默认使用轻量模式：小修小改不创建开发目录，不写开发日志，必要记录交给 git diff / commit message。
- `docs/superpowers/` 只用于存放尚未进入开发工作流的候选需求、设计草案、PRD 候选和点子；默认不读，只有用户明确点名或明确要推进为开发任务时才读取。
- `docs/superpowers/` 中的内容只能视为候选方案，不得直接当作当前需求执行；要采纳时先按 `WORKFLOW.md` 固化范围，必要时迁入 `docs/develops/`。
- 长任务模式按 `WORKFLOW.md` 执行：使用 `docs/develops/current.json` 定位活跃需求或阶段目录，并更新 `docs/develops/<active>/current.md`。
- 如果用户没有明确要求长任务模式，但需求预计跨多个会话、超过 3 个可验证任务或跨前后端/API/数据库/架构，先询问是否进入长任务模式。
- 长任务模式中 task 进入 `done` 后必须 git commit；阶段切换前如已有可验证成果，也要先 commit。
- 长任务在标记完成前，必须检查并同步本次需求涉及的入口文档：优先看 `README.md`、相关 `memory-bank/*.md`、deployment/runbook 和示例命令；不要漏掉新增命令、脚本、公开行为和运维步骤。
- `docs/develops/<active>/current.md` 只保留当前需求的接手上下文，写轻量备注，不写流水账。
{AGENTS_END}"""


def repo_root(cwd: str | None) -> Path:
    return Path(cwd or ".").resolve()


def write_text(path: Path, content: str, *, force: bool) -> str:
    if path.exists() and not force:
        return f"skip existing {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"write {path}"


def write_json(path: Path, data: object, *, force: bool) -> str:
    return write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n", force=force)


def remove_path(path: Path) -> str:
    if not path.exists():
        return f"skip missing {path}"
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return f"remove {path}"


def extract_between(text: str, start: str, end: str) -> str | None:
    pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.S)
    match = pattern.search(text)
    return match.group(1) if match else None


def merge_workflow(existing: str | None) -> str:
    custom = ""
    if existing:
        found = extract_between(existing, WORKFLOW_CUSTOM_START, WORKFLOW_CUSTOM_END)
        if found is not None:
            custom = found
        else:
            custom = "\n<!-- Legacy local WORKFLOW.md preserved during update. -->\n\n" + existing.rstrip() + "\n"
    placeholder_compact = f"{WORKFLOW_CUSTOM_START}{WORKFLOW_CUSTOM_END}"
    placeholder_spaced = f"{WORKFLOW_CUSTOM_START}\n\n{WORKFLOW_CUSTOM_END}"
    replacement = f"{WORKFLOW_CUSTOM_START}{custom}{WORKFLOW_CUSTOM_END}"
    if placeholder_compact in WORKFLOW_MD:
        return WORKFLOW_MD.replace(placeholder_compact, replacement)
    return WORKFLOW_MD.replace(placeholder_spaced, replacement)


def merge_agents(existing: str | None) -> str:
    if not existing:
        return AGENTS_BLOCK + "\n"
    pattern = re.compile(re.escape(AGENTS_START) + r".*?" + re.escape(AGENTS_END), re.S)
    if pattern.search(existing):
        return pattern.sub(AGENTS_BLOCK, existing)
    suffix = "" if existing.endswith("\n") else "\n"
    return existing + suffix + "\n" + AGENTS_BLOCK + "\n"


def read_current_state(root: Path) -> dict[str, object]:
    current_path = root / "docs/develops" / "current.json"
    if not current_path.exists():
        return {}
    return json.loads(current_path.read_text(encoding="utf-8"))


def feature_root_from_active(active: str | None) -> str | None:
    if not active:
        return None
    return Path(active).parts[0]


def ensure_templates(root: Path) -> None:
    templates = root / "docs/develops" / "_template"
    if not templates.exists():
        install_or_update(root, force=False, update=False)


def copy_templates(root: Path, target: Path, *, force: bool) -> list[str]:
    actions: list[str] = []
    for filename in ["task.json", "current.md"]:
        source = root / "docs/develops" / "_template" / filename
        destination = target / filename
        if destination.exists() and not force:
            actions.append(f"skip existing {destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        actions.append(f"write {destination}")
    return actions


def install_or_update(root: Path, *, force: bool, update: bool) -> list[str]:
    actions: list[str] = []
    workflow_path = root / "WORKFLOW.md"
    if update:
        existing = workflow_path.read_text(encoding="utf-8") if workflow_path.exists() else None
        actions.append(write_text(workflow_path, merge_workflow(existing), force=True))
    else:
        actions.append(write_text(workflow_path, merge_workflow(None), force=force))

    actions.append(write_json(
        root / "docs/develops" / "current.json",
        {
            "active": None,
            "updated_at": date.today().isoformat(),
            "status": "idle",
        },
        force=force and not update,
    ))
    actions.append(write_json(root / "docs/develops" / "task.schema.json", TASK_SCHEMA, force=force or update))
    actions.append(write_json(root / "docs/develops" / "_template" / "task.json", TASK_TEMPLATE, force=force or update))
    actions.append(write_text(root / "docs/develops" / "_template" / "current.md", CURRENT_TEMPLATE, force=force or update))
    actions.append(write_text(root / "docs/superpowers" / "README.md", SUPERPOWERS_README, force=False))
    for filename, content in MEMORY_BANK_FILES.items():
        actions.append(write_text(root / "memory-bank" / filename, content, force=False))
    if update or force:
        actions.append(remove_path(root / "docs/develops" / "_template" / "progress.md"))

    agents_path = root / "AGENTS.md"
    existing_agents = agents_path.read_text(encoding="utf-8") if agents_path.exists() else None
    actions.append(write_text(agents_path, merge_agents(existing_agents), force=True))
    return actions


def check(root: Path) -> int:
    required = [
        "WORKFLOW.md",
        "docs/develops/current.json",
        "docs/develops/task.schema.json",
        "docs/develops/_template/task.json",
        "docs/develops/_template/current.md",
        "docs/superpowers/README.md",
        "memory-bank/README.md",
        "memory-bank/product.md",
        "memory-bank/tech-stack.md",
        "memory-bank/api-contract.md",
        "memory-bank/architecture.md",
        "memory-bank/deployment.md",
    ]
    deprecated = ["docs/develops/_template/progress.md"]
    missing = [path for path in required if not (root / path).exists()]
    present_deprecated = [path for path in deprecated if (root / path).exists()]
    agents = root / "AGENTS.md"
    agents_ok = agents.exists() and AGENTS_START in agents.read_text(encoding="utf-8")
    if missing:
        print("missing:")
        for path in missing:
            print(f"- {path}")
    if present_deprecated:
        print("deprecated managed files:")
        for path in present_deprecated:
            print(f"- {path}")
    print(f"AGENTS.md managed block: {'ok' if agents_ok else 'missing'}")
    return 1 if missing or present_deprecated or not agents_ok else 0


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "feature"


def new_feature(root: Path, name: str, *, day: str | None, force: bool) -> list[str]:
    current_day = day or date.today().isoformat()
    dirname = f"{current_day}-{slugify(name)}"
    target = root / "docs/develops" / dirname
    if target.exists() and not force:
        raise SystemExit(f"feature directory already exists: {target}")

    ensure_templates(root)
    target.mkdir(parents=True, exist_ok=True)
    actions = copy_templates(root, target, force=force)
    actions.append(write_json(
        root / "docs/develops" / "current.json",
        {
            "active": dirname,
            "updated_at": current_day,
            "status": "in_progress",
        },
        force=True,
    ))
    return actions


def new_phase(root: Path, name: str, *, feature: str | None, force: bool) -> list[str]:
    current_state = read_current_state(root)
    current_active = current_state.get("active")
    active_feature = feature_root_from_active(current_active) if isinstance(current_active, str) else None
    feature_dir = feature or active_feature
    if not feature_dir:
        raise SystemExit("feature directory is required when there is no active demand")

    feature_path = root / "docs/develops" / feature_dir
    if not feature_path.exists():
        raise SystemExit(f"feature directory does not exist: {feature_path}")

    ensure_templates(root)
    phase_slug = slugify(name)
    target = feature_path / phase_slug
    if target.exists() and not force:
        raise SystemExit(f"phase directory already exists: {target}")

    target.mkdir(parents=True, exist_ok=True)
    actions = copy_templates(root, target, force=force)
    actions.append(write_json(
        root / "docs/develops" / "current.json",
        {
            "active": target.relative_to(root / "docs/develops").as_posix(),
            "updated_at": date.today().isoformat(),
            "status": "in_progress",
        },
        force=True,
    ))
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Svenstar dual-mode develop workflow.")
    parser.add_argument("--cwd", help="Target repository root. Defaults to current directory.")
    sub = parser.add_subparsers(dest="command", required=True)

    install_parser = sub.add_parser("install", help="First-time setup.")
    install_parser.add_argument("--force", action="store_true", help="Overwrite existing managed files.")

    update_parser = sub.add_parser("update", help="Refresh managed files while preserving custom sections.")
    update_parser.add_argument("--force", action="store_true", help="Accepted for symmetry; update already refreshes managed files.")

    sub.add_parser("check", help="Check whether workflow files are installed.")

    feature_parser = sub.add_parser("new-feature", help="Create a new demand root directory under docs/develops/.")
    feature_parser.add_argument("name")
    feature_parser.add_argument("--date", help="Date prefix, defaults to today.")
    feature_parser.add_argument("--force", action="store_true", help="Overwrite existing feature files.")

    phase_parser = sub.add_parser("new-phase", help="Create a phase subdirectory under an existing demand root.")
    phase_parser.add_argument("name")
    phase_parser.add_argument("--feature", help="Existing feature root directory name under docs/develops/. Defaults to current active demand root.")
    phase_parser.add_argument("--force", action="store_true", help="Overwrite existing phase files.")

    args = parser.parse_args()
    root = repo_root(args.cwd)

    if args.command == "install":
        actions = install_or_update(root, force=args.force, update=False)
    elif args.command == "update":
        actions = install_or_update(root, force=True, update=True)
    elif args.command == "check":
        return check(root)
    elif args.command == "new-feature":
        actions = new_feature(root, args.name, day=args.date, force=args.force)
    elif args.command == "new-phase":
        actions = new_phase(root, args.name, feature=args.feature, force=args.force)
    else:
        raise AssertionError(args.command)

    for action in actions:
        print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
