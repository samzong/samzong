# gh-pr-review

一个面向“项目 Owner 视角”的 GitHub Pull Request 评审技能（skill）：用 `gh` 抓取 PR 元信息、diff、CI 状态与失败日志（best-effort），并生成一份可编辑的评审文档 `review-<pr>.md`（中文叙述 + 英文可复制 GitHub 评论）。

## 设计目标

- **Owner-grade**：以维护者/Owner 的责任标准审视变更（正确性、安全性、可维护性、回归风险、测试质量）。
- **只评 PR 引入的修改**：默认仅对 PR diff 里新增/修改/删除的行给出意见；不翻旧账、不对同文件未触及的历史代码吹毛求疵。
- **仁慈默认接受**：对开源贡献默认“尽可能接受”，但拒绝明显错误、无用代码、引入风险/漏洞的改动；指出问题时提供可执行建议而非指责。
- **确定性抓取 + 可人工编辑输出**：脚本负责“事实与材料齐全”，人/模型负责“理解 + 写评审”。
- **全程 `gh` 交互**：所有 GitHub API/页面数据都通过 `gh` 获取；若 `gh` 不存在或未认证，直接停止。

## 输入与输出

**输入**
- PR URL：`https://github.com/<org>/<repo>/pull/<n>`
- 或 PR number：`<n>`
  - 当只给数字时，会在当前目录解析 git remote（优先 `upstream`，否则 `origin`）推断 `owner/repo`，再用 `gh` 查询。

**输出**
- `review-<n>.md`
  - **中文**：评审叙述、结论、风险、建议
  - **英文**：逐条可复制粘贴到 GitHub 的 review comment 模板（带 `path:line`）
- `.gh-pr-review/pr-<n>/`（材料目录，便于追溯）
  - `pr.json`：PR 元信息（title/author/base/head/head SHA…）
  - `diff.patch`：unified diff（来自 `gh pr diff`）
  - `changed-lines.json`：从 diff 解析出的“变更行号映射”（用于强制 review scope）
  - `checks.txt`：checks/CI 摘要（优先 `gh pr checks`，失败则 fallback）
  - `failed-logs.txt`：失败 job 日志（best-effort；无失败或无法抓取会说明）

## 工作流程（文本绘图）

```
┌─────────────────────┐
│  User provides PR   │
│  URL or PR number   │
└─────────┬───────────┘
          │
          v
┌──────────────────────────────────────────────┐
│ scripts/gh_pr_review.sh                       │
│ - hard gate: gh exists + gh auth ok           │
│ - resolve repo (from URL or git remotes)      │
└─────────┬────────────────────────────────────┘
          │
          v
┌──────────────────────────────────────────────┐
│ Fetch facts via gh                            │
│ - gh pr view  -> pr.json                      │
│ - gh pr diff  -> diff.patch                   │
│ - gh pr checks / fallback -> checks.txt       │
│ - gh run view (failed only) -> failed-logs.txt│
└─────────┬────────────────────────────────────┘
          │
          v
┌──────────────────────────────────────────────┐
│ scripts/parse_unified_diff.py                 │
│ - parse @@ hunks                              │
│ - compute new-side line numbers for additions │
│ - compute old-side line numbers for deletions │
│ -> changed-lines.json                         │
└─────────┬────────────────────────────────────┘
          │
          v
┌──────────────────────────────────────────────┐
│ scripts/generate_review_md.py + template      │
│ - render review-<n>.md skeleton               │
│ - include in-scope hunk/line hints            │
└─────────┬────────────────────────────────────┘
          │
          v
┌──────────────────────────────────────────────┐
│ Human/Agent fills review-<n>.md               │
│ - Chinese narrative                           │
│ - English copy-paste comments                 │
│ - decide: Recommend merge / Request changes   │
└──────────────────────────────────────────────┘
```

## 如何使用

在任意目录执行（推荐在一个 git repo 里执行，这样输入 PR number 时可自动解析 repo）：

```bash
./scripts/gh_pr_review.sh https://github.com/vllm-project/semantic-router/pull/890
```

或（在对应仓库目录下）仅输入 PR number：

```bash
./scripts/gh_pr_review.sh 890
```

生成完成后，打开 `review-890.md`，把其中英文评论块直接复制到 GitHub Review 评论即可。

## 安装方式

### 1) OpenAI Codex（Codex CLI / Codex Skills）

用 Codex 自带的 skill installer（推荐）：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/samzong/samzong/tree/main/skills/gh-pr-review
```

安装后重启 Codex。

也可以手工安装：把整个目录复制到 `~/.codex/skills/gh-pr-review/`。

### 2) Claude Code（Anthropic）

Claude Code 支持“技能/插件”生态，常见做法包括：

- **手工安装（最通用）**：将目录复制到本机的 Claude skills 目录（常见位置：`~/.claude/skills/gh-pr-review/` 或项目内 `.claude/skills/gh-pr-review/`）。
- **使用 Claude Code 的插件/marketplace 机制**：将仓库注册为 marketplace 后安装（不同版本/发行渠道的命令可能略有差异）。

如果你不确定本机 Claude Code 的 skills 目录位置，优先用手工方式，并在 Claude Code 的文档/设置里确认其自动发现路径。

## 依赖与注意事项

- 必须安装并配置 `gh`，且对目标仓库有访问权限：`gh auth status -h github.com` 需成功。
- 本 skill 会抓取并落地 PR diff / checks / 日志到本地文件；请只在可信环境运行，并避免对不可信 PR 运行带有执行副作用的脚本。
- 行号来自 unified diff 的 new-side 计算：适合做“对齐变更范围”的评审引用；对纯删除行（old-side）会标注 old line（通常不建议在 GitHub 上对删除行做 inline comment，可作为说明依据）。
