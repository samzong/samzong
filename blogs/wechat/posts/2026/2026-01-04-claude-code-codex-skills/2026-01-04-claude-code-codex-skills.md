# Agent Skills：让 AI Coding Agent 真正"懂"你的工作流

## 前言

我算是比较深入使用 Claude Code 和 OpenAI Codex 写代码的一派；这一年技术栈也是迭代了不少：

- 从最开始研究 `CLAUDE.md` 到 `Cursor Rules` 到 `AGENT.md`。
- 从手工维护 `PLAN.md`、`DESIGN.md`、`TODO.md` 到 `Kiro Specs` 到 Github 推出了 `spec-kit`。
- 从尝试各种 `MCP`，`Sub Agent`，最后到现在的 `Skills`。

(虽然现在 Antigravity 走的是 Rules + Workflow 的路子，但我觉得最终还是会有一个统一的机制，比如 Skills)

Vibe Coding 一直在解决的几个问题：项目规范，使用新语言规范，长上下文编程。

- 上下文对齐与认知偏差
- 非线性任务的长期记忆与状态管理
- 工具使用的边界与组合爆炸
- 自然语言意图到工程实现的降噪

最近算是比较深入的使用了下 `Claude 推出的 Agent Skills`，觉得这个机制很有趣，所以写篇文章分享下我的使用心得。

## Agent Skills 是什么？

Agent Skills（下面简称 Skills） 可以简单理解是给 Claude Code 和 Codex 提供的一种"技能包"，最开始由 Claude 推出，后来 Codex 也支持了。

![](https://fastly.jsdelivr.net/gh/bucketio/img10@main/2026/01/05/1767545401723-5118be54-403e-45fe-8b8a-e6803450fb26.png)

**它不是对话上下文里的 prompt，而是一个持久化的、结构化的工作流定义。** 当任务触发特定场景时，AI 会自动加载对应的 Skill，按照预设流程执行。

## Claude Code 的 Skills

Claude Code 通过 `CLAUDE.md` 文件提供项目级别的自定义指令，而 Skills 则是更进一步的**任务级别工作流定义**。

一个 Skill 通常包含：
- `SKILL.md`：技能的元数据和执行逻辑
- `references/`：参考资料（可选）
- `scripts/`：配套脚本（可选）
- `assets/`：资源文件（可选）

Skills 存放位置：
- 全局：`~/.claude/skills/`
- 项目级：`.claude/skills/`

当用户的请求匹配 Skill 的 `description` 时，Claude 会自动应用该 Skill。

## OpenAI Codex 的 Skills

Codex 的实现类似，通过 `AGENTS.md` 提供项目指令，Skills 存放在 `~/.codex/skills/` 目录下。

Skill 的触发方式：
- **显式调用**：用 `/skills` 命令或 `$skill-name` 引用
- **隐式触发**：当任务匹配 Skill 的 description 时自动激活

# 我主要使用的 Skills

我的 `~/.codex/skills/` 目录下有这些 Skills：

## brainstorming - 创意脑暴

> **用途**：任何创造性工作（新功能设计、组件开发、行为修改）之前，先进行结构化的需求探索和设计。

**核心流程**：
- 理解当前项目上下文（文件、文档、最近提交）
- **一次只问一个问题**（偏好选择题）
- 提出 2-3 个不同实现方案及其权衡
- 分段呈现设计（每段 200-300 字），逐段确认
- 输出设计文档到 `docs/plans/YYYY-MM-DD-<topic>-design.md`

以前直接让 AI 写代码，结果经常偏。现在强制走脑暴流程后，产出的设计更符合预期。**"一次只问一个问题"这个原则值得学习**。

这个其实也算是 `specs workflow` 的一个实现。

---

## content-research-writer - 内容写作助手

> **用途**：写博客、技术文章、教程时的协作伙伴。

**核心能力**：
- 协作大纲（Collaborative Outlining）
- 研究辅助（找资料、加引用）
- 改进开头 Hook
- 逐章节反馈
- 引用管理（inline、numbered、footnote）

**文件组织建议**：
```bash
~/.codex/skills ls
brainstorming            doc-coauthoring          github-issue-reader      requesting-code-review   wechat-tech-article
clig-eval-prompt         doc-consistency-reviewer local                    systematic-debugging
content-research-writer  gh-pr-review             receiving-code-review    test-driven-development
```

## doc-consistency-reviewer

> **用途**：检查文档和代码/配置之间的不一致。

**产出**：至少 30 个问题的审计报告，每个问题包含：
- 证据（文档片段 + 代码/配置片段 + 文件路径行号）
- 严重程度（P0-P3）
- 简短修复建议

代码库大了之后，文档过时是常态。这个 Skill 强制要求"至少找 30 个问题"：**要求严苛才能发现问题**。

---

## systematic-debugging

> **用途**：遇到 bug 时，强制走结构化调试流程。

**核心原则**：
```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

**四阶段流程**：
1. **Root Cause Investigation**：读错误信息、复现、检查最近改动、收集证据
2. **Pattern Analysis**：找到 working examples，对比差异
3. **Hypothesis and Testing**：形成单一假设，最小化测试
4. **Implementation**：先写失败测试，再修复

**三次修复失败规则**：如果连续 3 次修复都失败，**停下来质疑架构**而不是继续打补丁。

严谨的调试流程定义：**随机改代码 + 看测试通不通过是最浪费时间的做法**。这个 Skill 把调试变成了一个可重复的科学方法。

---

## test-driven-development

> **用途**：任何功能实现或 bug 修复前，先写失败测试。

**核心原则**：
```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

**常见借口 vs 现实**：

| 借口 | 现实 |
|------|------|
| "太简单不需要测试" | 简单代码也会坏。测试只需 30 秒。 |
| "我先写之后再测" | 事后写的测试立即通过，证明不了什么。 |
| "我手动测过了" | Ad-hoc 测试无记录、不可重复。 |
| "删掉 X 小时工作太浪费" | 沉没成本谬误。不可信的代码才是浪费。 |

TDD 的争议很大，但这个 Skill 说得很清楚：**"I'll test after" 和 "Test first" 回答的是完全不同的问题**。
前者问"这代码做了什么"，后者问"这代码应该做什么"。

---

# 我开发的 Skills

## clig-eval-prompt

因为写 CLI 工具挺多的，所以我开发了这个 Skill。每次评审 CLI 项目时都要手动参照这份指南，效率很低。

**用途**：根据 CLIG 指南生成标准化的 CLI 评审 prompt，包含：
- 13 个评审维度（A-M），加权评分
- 硬性门槛（触发则直接降级）
- 严重程度阈值（≥85 生产级、70-84 可用、55-69 不推荐、<55 不合格）

**评审维度示例**：
- A 基础契约与可组合性（18%）：退出码、stdout/stderr 规范
- D 交互与危险操作（10%）：TTY 感知、确认机制、--no-input
- H 配置/环境变量/安全（10%）：XDG 规范、敏感信息处理

**使用方式**：
```md
使用 clig-eval-prompt 评审 my-cli-tool
```

Skill 会自动加载 `references/prompt.md` 中的标准 prompt 并执行评审。

---

## gh-pr-review

> **背景**：作为项目 maintainer，评审 PR 是日常工作。但每次都要手动看 diff、检查 CI、写评论，很繁琐。

**用途**：
- 输入：PR URL 或 PR number
- 输出：`review-<n>.md`

**工作流程**：
1. 用 `gh` CLI 抓取 PR 元信息、diff、CI 状态、失败日志
2. 识别变更涉及的模块，只读相关代码
3. 检查 CI 失败是否由 PR 引起
4. 应用"当前版本"最佳实践（避免过时建议）
5. 生成评审文档

**核心原则**：
- **只评 PR 引入的改动**——不翻旧账
- **默认接受**——除非有明确 bug、安全问题或回归风险
- **给出可执行建议**——不是"这样不好"，而是"建议改成 xxx"

**配套脚本**：
- `gh_pr_review.sh`：抓取所有 PR artifacts
- `parse_unified_diff.py`：解析 diff，计算变更行号映射
- `generate_review_md.py`：生成 review 文档骨架

---

# 写在最后

Claude Code 和 Codex 的 Skills 机制，让我从"一个人和 AI 聊天"变成了"一个人带着一套经过验证的工作流在执行"。

> 好的 Skill 设计应该是"约束"而非"自由"

好的 Skill 应该是高度结构化的——**强制走特定流程、禁止跳过关键步骤、明确定义输出格式**。AI 擅长执行明确指令，不擅长"看情况判断"。

> 社区 Skills 是起点，自定义 Skills 才是终点

我最开始用的 Skills 大部分来自社区或官方示例。它们解决的是通用问题。

但真正提效的是那 2 个我自己开发的 Skills：**它们是针对我自己的工作场景、我自己的项目规范定制的**。

如果你只是用别人的 Skills，那只是"用上了这个功能"；只有当你开始写自己的 Skills，才算真正"掌握了这个能力"。

---

**AI 不是替代人类，而是放大人类的能力。** 我的观点还是 AI 会让你产生 10x 乃至更高的加速度，而不是取代你。

# 小技巧

其实可以基于你与 Claude Code 或者 Codex 的对话的工作模式，让他为你创建一个 Skills。
