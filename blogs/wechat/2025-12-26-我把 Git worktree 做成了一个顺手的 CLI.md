# gmc：给自己做的 Git 效率工具箱

![Image](https://raw.githubusercontent.com/samzong/gmc/main/logo.png)

最近把自己常用的几个 Git 操作封装成了一个 CLI 工具，叫 `gmc`（Git Message Commit）。

项目地址：https://github.com/samzong/gmc

核心能力三个：

- `gmc`：读 staged diff，用 LLM 生成 Conventional Commits 风格的提交信息
- `gmc wt`：一键管理 worktree，多方案并行开发
- `gmc tag`：规则 + 大模型，给出合理的语义化版本号建议

这篇文章重点聊聊 `gmc wt`——这个是我后来补上的，用得最多。

---

**01**

## 自动生成 Commit Message

这是 `gmc` 最早做的功能。读 staged diff，调 LLM 生成 Conventional Commits 风格的提交信息，给个交互确认 `y/n/r/e`。

```bash
# 标准用法
git add -A
gmc

# 懒人模式，自动 git add
gmc -a

# 只提交指定文件
gmc -a path/to/file1 path/to/file2

# 追加 issue 引用
gmc --issue 123

# 临时加约束
gmc --prompt "Focus on user-visible behavior"

# 只生成不提交
gmc --dry-run
```

还有个 stdin 模式：

```bash
git diff | gmc -
```

可以把 `gmc` 当成 diff → commit message 的转换器。

---

**02**

## worktree 管理：gmc wt

用大模型写代码之后，我越来越习惯一个模式：同一个需求，同时跑 2～3 条路线，甚至让不同的 Agent 各写一版，最后挑一个最好的合并。

但只用 `git checkout` 切分支很快就乱了：

- A 分支跑到一半，B 分支也想试试，但 A 还没提交
- 两边都要跑测试起服务，一直来回切
- 想并行推进，却被一个工作目录绑死了

Git 有 `git worktree` 解决这个问题：同一个仓库可以同时有多个目录，每个目录对应一个分支，互不干扰。但原生命令有点烦，所以我做了 `gmc wt`。

### 2.1 把仓库 clone 成 `.bare + worktree` 结构

如果要把 worktree 当常态用，推荐直接用 `.bare` 模式：仓库本体是 bare repo，每个分支对应一个 worktree 目录。

```bash
gmc wt clone https://github.com/user/repo.git --name my-project
```

会创建 `.bare/` 目录和默认分支的工作区（比如 `main/`），后续就可以随便开分支开目录。

### 2.2 开源贡献场景：clone + upstream 一步到位

给开源项目提 PR（fork + upstream）最烦的一步：clone 完 fork 还要手动加 upstream remote。

`gmc wt clone` 支持 `--upstream`：

```bash
gmc wt clone https://github.com/me/my-fork.git \
  --upstream https://github.com/org/upstream-repo.git \
  --name upstream-repo
```

后续在默认分支工作区里同步 upstream，再开新 feature worktree 就行。

### 2.3 一键多开工作区：gmc wt dup

这个是我用得最多的。

同时跑多个实现、挑一个最好的保留：

```bash
gmc wt dup 3 -b main
```

创建 3 个临时 worktree，每个有自己的临时分支，在不同目录里同时推进，互不影响。

### 2.4 把临时分支扶正：gmc wt promote

评估完之后，把最好的那套提升为正式分支：

```bash
gmc wt promote .dup-1 feature/best-solution
```

本质就是重命名临时分支，把一次并行实验变成可维护的分支。

### 2.5 其他常用命令

```bash
gmc wt list
gmc wt add feature-login -b main
gmc wt remove feature-login
gmc wt remove feature-login -D
```

---

**03**

## 版本号建议：gmc tag

做这个功能的原因：我不喜欢那种"只要有一个 feat 就直接升 minor"的策略。一个 feat 可能就是加个可选参数、补个小能力。

`gmc tag` 的思路：

1. 先用规则引擎给一个保守且可解释的版本建议
2. 如果配了 API Key，再问大模型哪个版本更合适
3. LLM 结果会校验，有兜底，不会出现版本倒退

```bash
gmc tag
gmc tag --yes
```

---

**04**

## 安装

### Homebrew

```bash
brew tap samzong/tap
brew install gmc
```

### 初始化配置

提交信息生成需要配置 API Key：

```bash
gmc init
```

或者手动：

```bash
gmc config set apikey YOUR_OPENAI_API_KEY
gmc config set apibase https://your-proxy-domain.com/v1
gmc config set model gpt-4.1-mini
```

几个细节：

- macOS/Linux 上配置文件会被设为 `0600` 权限
- 支持在仓库里放 `.gmc.yaml` 做项目级覆盖

---

**05**

## 其他

- `--branch`：根据描述生成分支名并切换
- OpenAI 兼容接口支持
- GitHub Action：仓库里有 `action.yml`，可以在 CI 里用

---

**写在最后**

`gmc` 的核心就一个目标：让并行开发更顺手。

开始习惯多开几个工作区之后，会发现 AI 辅助开发的收益明显变大了——因为你终于可以把不同方案真正跑起来对比，而不是在一个目录里反复切换打断自己的思路。

项目地址：https://github.com/samzong/gmc
