# Claude Code 和 Codex 的 Skills：让 AI Coding Agent 真正"懂"你的工作流

> 当 AI 不再只是补全代码，而是成为一个能理解项目规范、执行完整工作流程的队友

## 前言

用 Claude Code 和 OpenAI Codex 写代码已经有一段时间了。最开始只是拿它们当高级自动补全用，后来发现一个问题：**每次提问都要重复说明"我们项目用的是 xx 规范"、"PR 评审要按这个流程来"、"错误要这么处理"**——太累了。

直到我开始用 **Skills**，一切都变了。

Skills 是 Claude Code 和 Codex 都支持的一种"技能包"机制。**它不是对话上下文里的 prompt，而是一个持久化的、结构化的工作流定义。** 当任务触发特定场景时，AI 会自动加载对应的 Skill，按照预设流程执行。

这篇文章会介绍：
1. Skills 到底是什么、怎么工作的
2. 我目前使用的 12 个 Skills（来自社区和自己定制）
3. 我自己开发的 2 个 Skills：`clig-eval-prompt` 和 `gh-pr-review`
4. 我的一些使用心得和观点

---

## Skills 是什么？

### Claude Code 的 Skills

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

### OpenAI Codex 的 Skills

Codex 的实现类似，通过 `AGENTS.md` 提供项目指令，Skills 存放在 `~/.codex/skills/` 目录下。

Skill 的触发方式：
- **显式调用**：用 `/skills` 命令或 `$skill-name` 引用
- **隐式触发**：当任务匹配 Skill 的 description 时自动激活

---

## 我正在使用的 12 个 Skills

我的 `~/.codex/skills/` 目录下有这些 Skills：

### 1. brainstorming - 创意脑暴

> **用途**：任何创造性工作（新功能设计、组件开发、行为修改）之前，先进行结构化的需求探索和设计。

**核心流程**：
- 理解当前项目上下文（文件、文档、最近提交）
- **一次只问一个问题**（偏好选择题）
- 提出 2-3 个不同实现方案及其权衡
- 分段呈现设计（每段 200-300 字），逐段确认
- 输出设计文档到 `docs/plans/YYYY-MM-DD-<topic>-design.md`

**我的观点**：这个 Skill 对我帮助很大。以前直接让 AI 写代码，结果经常偏。现在强制走脑暴流程后，产出的设计更符合预期。**"一次只问一个问题"这个原则值得学习**。

---

### 2. content-research-writer - 内容写作助手

> **用途**：写博客、技术文章、教程时的协作伙伴。

**核心能力**：
- 协作大纲（Collaborative Outlining）
- 研究辅助（找资料、加引用）
- 改进开头 Hook
- 逐章节反馈
- 引用管理（inline、numbered、footnote）

**文件组织建议**：
```
~/writing/article-name/
├── outline.md          # 大纲
├── research.md         # 研究材料
├── draft-v1.md         # 初稿
├── draft-v2.md         # 修订稿
├── final.md            # 定稿
└── sources/            # 参考资料
```

**我的观点**：这个 Skill 的设计很"人性化"——它不是一口气生成全文，而是分段写、分段 review。**写作就应该是一个迭代过程**，这点和写代码很像。

---

### 3. doc-coauthoring - 文档协作

> **用途**：写设计文档、技术提案、RFC、决策文档时的结构化工作流。

**三阶段流程**：
1. **Context Gathering**：收集所有相关上下文，问清楚需求
2. **Refinement & Structure**：逐章节头脑风暴、筛选、起草、迭代
3. **Reader Testing**：用一个"无上下文"的 Claude 测试文档是否能被读懂

**我的观点**：第三阶段的 "Reader Testing" 是这个 Skill 的亮点。**文档写完后让一个"不知道上下文"的 AI 来读，能发现很多盲点**。这个技巧我现在写任何重要文档都会用。

---

### 4. doc-consistency-reviewer - 文档一致性审计

> **用途**：检查文档和代码/配置之间的不一致。

**产出**：至少 30 个问题的审计报告，每个问题包含：
- 证据（文档片段 + 代码/配置片段 + 文件路径行号）
- 严重程度（P0-P3）
- 简短修复建议

**我的观点**：代码库大了之后，文档过时是常态。这个 Skill 强制要求"至少找 30 个问题"——**要求严苛才能发现问题**。

---

### 5. gh-pr-review - GitHub PR 评审

> **用途**：以项目 Owner 视角生成高质量 PR 评审文档。

这个是我自己开发的，后面详细介绍。

---

### 6. github-issue-reader - Issue 上下文获取

> **用途**：实现 Issue 前，先获取完整上下文（描述、所有评论、标签、关联 PR、交叉引用）。

**我的观点**：很多人 assign 了 Issue 就开始写代码，根本没看完所有评论。**这个 Skill 强制你先"读完再动手"**。

---

### 7. receiving-code-review - 接收代码评审反馈

> **用途**：正确地处理收到的 Code Review 反馈。

**核心原则**：
- **技术评估，而非情绪表演**
- 禁止说"You're absolutely right!"、"Great point!"（这是讨好）
- 先验证，再实现；先问清楚，再行动
- 如果反馈有问题，**有理有据地反驳**

**我的观点**：这个 Skill 的设计反映了一种成熟的工程文化：**评审是技术讨论，不是权力游戏**。评审者的建议也可能是错的，盲目执行只会引入更多问题。

---

### 8. requesting-code-review - 主动请求代码评审

> **用途**：完成任务后主动请求 review，而不是等别人找问题。

**强制点**：
- 每完成一个任务后 review（subagent-driven development）
- 每完成大功能后 review
- 合并前 review

**我的观点**：**Review early, review often**。这和 CI/CD 的理念一致——越早发现问题，修复成本越低。

---

### 9. systematic-debugging - 系统化调试

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

**我的观点**：这是我见过最严谨的调试流程定义。**随机改代码 + 看测试通不通过是最浪费时间的做法**。这个 Skill 把调试变成了一个可重复的科学方法。

---

### 10. test-driven-development - 测试驱动开发

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

**我的观点**：TDD 的争议很大，但这个 Skill 说得很清楚——**"I'll test after" 和 "Test first" 回答的是完全不同的问题**。前者问"这代码做了什么"，后者问"这代码应该做什么"。

---

### 11. clig-eval-prompt - CLI 设计评审  

这是我自己开发的，后面详细介绍。

---

### 12. local（其他辅助 Skills）

一些小工具性质的 Skills，不展开了。

---

## 我开发的 2 个 Skills

### 1. clig-eval-prompt - DevOps CLI 评审

> **背景**：我翻译并维护了 [clig.onev.dev](https://clig.onev.dev)（命令行界面设计指南中文版）。每次评审 CLI 项目时都要手动参照这份指南，效率很低。

**这个 Skill 的作用**：根据 CLIG 指南生成标准化的 CLI 评审 prompt，包含：
- 13 个评审维度（A-M），加权评分
- 硬性门槛（触发则直接降级）
- 严重程度阈值（≥85 生产级、70-84 可用、55-69 不推荐、<55 不合格）

**评审维度示例**：
- A 基础契约与可组合性（18%）：退出码、stdout/stderr 规范
- D 交互与危险操作（10%）：TTY 感知、确认机制、--no-input
- H 配置/环境变量/安全（10%）：XDG 规范、敏感信息处理

**使用方式**：
```
使用 clig-eval-prompt 评审 my-cli-tool
```

Skill 会自动加载 `references/prompt.md` 中的标准 prompt 并执行评审。

**我的观点**：**把专家知识编码成 Skill，让 AI 执行**——这才是 Skills 的正确打开方式。不是让 AI 乱猜，而是给它一个严格的框架。

---

### 2. gh-pr-review - GitHub PR 所有者级评审

> **背景**：作为项目 maintainer，评审 PR 是日常工作。但每次都要手动看 diff、检查 CI、写评论，很繁琐。

**这个 Skill 的设计**：
- 输入：PR URL 或 PR number
- 输出：`review-<n>.md`（中文分析 + 英文可复制粘贴评论）

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

**我的观点**：这个 Skill 体现了我对 Code Review 的理解——**评审是帮助贡献者成功，不是挑毛病**。同时，"只评变更行"这个限制也避免了无休止的"顺便改改这里"。

---

## 使用心得和观点

### 1. Skills 的本质是"编码的专家判断"

无论是 `systematic-debugging` 的四阶段流程，还是 `clig-eval-prompt` 的评审维度，都是把**人类专家的经验固化成机器可执行的规则**。

这和"写一个详细的 prompt"不同——prompt 是一次性的，Skill 是持久化的、可版本控制的、可迭代改进的。

### 2. 好的 Skill 设计应该是"约束"而非"自由"

我见过一些 Skill 写得很"开放"：给你介绍几个原则让你参考，具体怎么做看情况。

**这样的 Skill 几乎没用。**

好的 Skill 应该是高度结构化的——**强制走特定流程、禁止跳过关键步骤、明确定义输出格式**。AI 擅长执行明确指令，不擅长"看情况判断"。

### 3. 社区 Skills 是起点，自定义 Skills 才是终点

我用的 12 个 Skills 里，大部分来自社区或官方示例。它们解决的是通用问题。

但真正提效的是那 2 个我自己开发的 Skills——**它们是针对我自己的工作场景、我自己的项目规范定制的**。

如果你只是用别人的 Skills，那只是"用上了这个功能"；只有当你开始写自己的 Skills，才算真正"掌握了这个能力"。

### 4. Skills 是"AI Agent 的 SOP"

如果你在做自动化、做 Agent，Skills 就是给 Agent 定义的 SOP（标准作业程序）。

**没有 SOP 的 Agent 是危险的。** 它可能用错误的方式实现正确的目标，或者用正确的方式实现错误的目标。Skills 让 Agent 的行为可预测、可审计、可改进。

---

## 结语

Claude Code 和 Codex 的 Skills 机制，让我从"一个人和 AI 聊天"变成了"一个人带着一套经过验证的工作流在执行"。

**AI 不是替代人类，而是放大人类的能力。** Skills 把人类的专家经验编码成机器可执行的规则，让 AI 能够在特定领域达到"专家级"的执行质量。

如果你还没开始用 Skills，建议：
1. 先从社区 Skills 开始，体验一下结构化工作流的感觉
2. 然后针对自己的高频场景写一个 Skill——哪怕只是一个评审 checklist
3. 逐步建立自己的 Skills 库

你的 Skills 库，就是你的竞争壁垒。

## 小技巧

### 让 AI 总结你与他的对话，生成一个技能文档

基于你与 AI 对话的工作模式，让他总结出一个技能文档。


---

*本文提到的 Skills 可以在以下位置找到：*
- *社区 Skills：参考 [OpenAI Codex Skills 文档](https://platform.openai.com/docs/codex) 和 [Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code)*
- *我的自定义 Skills：[github.com/samzong/samzong/skills](https://github.com/samzong/samzong/tree/main/skills)*
