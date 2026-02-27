# Repo Local Skill Generator 设计规格

## 1. 目标

构建一个 `repo-local skill generator`。

用户在任意代码仓库内触发该生成器后，系统默认自动扫描当前仓库，分析真实的 `git` 与 `GitHub PR/review` 历史，生成两个本地 skill：

- `coding skill`：让 coding agent 尽量贴近该仓库当前真实接受的编码风格与工程习惯。
- `review skill`：让 review agent 尽量贴近该仓库核心 maintainer 的真实 review 风格、阻塞标准与关注点。

本系统追求的是：

- 高保真拟合
- 可解释
- 可审计
- 可重复生成

本系统**不承诺**虚假的 `100% 模仿`。

## 1.1 Language Requirement

生成器产出的所有内容统一使用英文。

包括：

- `SKILL.md`
- `profiles/` 下的画像与摘要
- `references/` 下的证据文档
- 规则、反例、排除项、代表性例子

这样做是为了避免执行层和证据层语言混杂，并提升跨仓库复用性。

## 2. 默认行为

- 在当前仓库触发后，默认自动扫描当前仓库。
- 默认生成 `1 个 coding skill + 1 个 review skill`。
- 若仓库复杂度明显较高，可升级为多个 `coding skill`，但默认不主动拆分。
- 若用户显式指定某个模块，仅生成该模块的 `coding skill`。
- 生成器支持定期重跑。
- 重跑时默认强覆盖生成器自己管理的 skill。

## 3. 非目标

以下内容不属于第一版目标：

- 通用到“任何仓库都能百分百复刻某个作者人格”
- 生成一套没有证据来源的黑盒 prompt
- 依赖人工长期维护生成结果
- 强行将所有仓库都拆成多个 coding skill
- 覆盖或修改用户自己维护的其他本地 skill

## 4. 输出路径与目录策略

### 4.1 Repo-local 路径

- 真实 skill 内容放在：`repo/.agents/skills/`
- 兼容路径为软链接：`repo/.claude/skills -> repo/.agents/skills`

理由：

- `repo/.agents/skills/` 作为 repo 内 canonical source，便于统一抽象。
- `repo/.claude/skills` 作为当前已知可发现路径的兼容层。
- 避免维护两份真实副本导致内容漂移。

### 4.2 覆盖规则

- 生成器只覆盖自己创建和管理的 skill。
- 不触碰用户其他 skill。
- 若 `repo/.claude/skills` 不存在，则创建软链接。
- 若 `repo/.claude/skills` 存在但不是指向 `repo/.agents/skills` 的软链接，则修正为正确软链接。

## 5. 系统分层

系统固定拆成四层：

1. `collector`
2. `profiler`
3. `skill generator`
4. `verifier`

### 5.1 Collector

职责：

- 采集原始事实
- 不做高层风格判断

输入：

- 当前仓库路径
- 可选模块范围

数据源：

- 本地 `git log`
- 本地 `git show` / `git diff`
- 作者贡献统计
- 文件路径、语言、目录分布
- `gh` 拉取的 PR、review、review comments、merge 信息、review request 信息

输出：

- 原始样本缓存
- 过滤后的有效样本集合
- 元数据摘要

### 5.2 Profiler

职责：

- 将原始样本压缩成结构化画像

输出：

- `coding profile`
- `review profile`

### 5.3 Skill Generator

职责：

- 根据 profile 生成 repo-local skill
- 控制目录、命名、证据层、软链接

### 5.4 Verifier

职责：

- 验证输出路径是否正确
- 验证软链接是否正确
- 验证 skill 结构是否完整
- 验证证据层是否齐全

## 6. 样本选择规则

## 6.1 Coding 样本

默认原则：`近期优先 + 子系统历史补齐`

- 默认至少分析最近半年提交。
- 按语言、目录、子系统切分样本。
- 在每个子系统中识别核心作者群。
- 如果某子系统半年内样本不足，则回退到该子系统全历史。
- 不用全仓库历史去污染某个冷门子系统。

样本重点：

- 真实代码 diff
- 真实文件修改路径
- 真实重构方式

样本噪音：

- 纯 commit message
- 无实际代码意义的空改动
- 与目标子系统无关的提交

## 6.2 Review 样本

默认原则：`有效 review 优先`

- 目标不是抓 `100 个 PR`。
- 目标是凑够最近一段时间内 `100 个有效 review 的 PR`。
- 若仓库不足 `100` 个有效 review PR，则退化为全量有效 PR。

必须过滤：

- bot review
- AI review
- 自动化评论
- 纯直合并且没有真实 review 过程的 PR
- 没有真实 review 行为的样本

有效 review PR 的最低条件：

- 存在真实人工 review 行为
- review 参与者不是 bot/自动化账号
- PR 中能观察到真实的 approve / request changes / review discussion / review request / merge 过程中的一部分或多部分

## 7. 核心画像规则

## 7.1 Coding Profile

`coding profile` 需要提炼以下维度：

- 命名习惯
- 目录与模块边界
- 文件粒度
- 函数粒度
- 错误处理模式
- 测试补充习惯
- 注释密度与风格
- 常见重构路径
- 常见增量修改方式
- 明确禁忌模式

画像目标不是“文学化描述开发者个性”，而是沉淀对 agent 真正有用的可执行约束。

输出应尽量结构化，例如：

- 规则
- 证据
- 频率
- 反例
- 排除原因

## 7.2 Review Profile

`review profile` 需要提炼以下维度：

- 核心 maintainer 群
- 高频关注问题
- 阻塞标准
- 可接受与不可接受改动的边界
- 经常要求补充的测试类型
- 经常要求补充的文档类型
- 评论语气与表达习惯
- 对设计、命名、错误处理、测试、兼容性的典型要求

核心 maintainer 默认通过纯行为识别：

- 经常 approve
- 经常 request changes
- 经常被请求 review
- 经常参与阻塞性讨论
- 经常推动最终 merge

## 8. 证据层要求

每个生成 skill 必须自带详尽证据层。

证据层不是可选附件，而是生成结果的一部分。

建议内容至少包括：

- 样本范围
- 时间窗口
- 有效样本统计
- 排除项统计
- 核心作者/maintainer 识别结果
- 提炼出的规则清单
- 代表性例子
- 反例
- 排除原因

目标：

- 让用户能检查 skill 为什么这么写
- 让后续重跑时能比较差异
- 让调试和改进不依赖猜

## 9. Skill 目录结构

第一版生成结果采用薄 `SKILL.md` + 厚证据层结构。

建议目录形态：

```text
.agents/
  skills/
    <repo>-coding/
      SKILL.md
      profiles/
        coding-profile.json
        coding-summary.md
      references/
        evidence.md
        anti-patterns.md
        examples.md
    <repo>-review/
      SKILL.md
      profiles/
        review-profile.json
        review-summary.md
      references/
        evidence.md
        blocking-patterns.md
        examples.md
```

若是模块级 coding skill：

```text
.agents/
  skills/
    <repo>-coding-<module>/
```

## 10. 命名规则

命名不能写死成：

- `repo-coding-skill`
- `repo-review-skill`

这类名字太蠢，无法扩展。

推荐规则：

- 仓库级 coding skill：`<repo>-coding`
- 模块级 coding skill：`<repo>-coding-<module>`
- 仓库级 review skill：`<repo>-review`

命名目的：

- 明确归属
- 支持未来多模块并存
- 便于生成器识别哪些 skill 归自己管理

## 11. 默认交互方式

默认入口采用零配置模式：

- 用户在当前仓库触发生成器
- 系统自动扫描当前仓库
- 默认生成 `1 coding + 1 review`

特殊分支：

- 若用户显式指定模块，则只生成该模块的 coding skill
- 若系统判定仓库复杂且存在明显多子系统稳定风格，可提出是否拆成多个 coding skill

## 12. 复杂仓库处理策略

第一版默认不把复杂仓库自动拆爆。

处理原则：

- 大多数仓库：`1 coding + 1 review`
- 显著复杂仓库：可升级为多个 coding skill
- 升级前可询问用户确认
- review skill 仍默认保持仓库级，因为其门槛来自核心 maintainer 群

## 13. 验证要求

生成完成后至少验证以下内容：

- `repo/.agents/skills/` 存在
- `repo/.claude/skills` 为正确软链接
- 生成的两个 skill 目录存在
- `SKILL.md` 存在
- `profiles/` 存在
- `references/` 存在
- 证据层文件齐全
- 仅覆盖生成器管理的 skill

## 14. 第一版建议的实现边界

第一版应该先把以下能力做扎实：

- 当前仓库自动扫描
- coding/review 样本收集与过滤
- 核心作者群识别
- 核心 maintainer 行为识别
- 两类 profile 生成
- 两个本地 skill 生成
- repo-local 路径与软链接修正
- 强覆盖但仅限受管 skill

第一版可以暂缓过度复杂的内容：

- 非 GitHub 平台适配
- 超细粒度 reviewer 分簇
- 跨仓库风格迁移
- 复杂 UI

## 15. 风险与约束

### 15.1 风格漂移

同一仓库、同一作者的风格会随时间和子系统变化。

缓解：

- 近期优先
- 子系统切分
- 反例保留

### 15.2 噪音污染

review 数据里 bot、自动化评论很多。

缓解：

- 强过滤
- 明确“有效 review”定义

### 15.3 黑盒生成

如果只有结论没有证据，后面无法维护。

缓解：

- 强制证据层

### 15.4 目录兼容性

不同工具的 repo-local 发现路径并不完全一致。

缓解：

- 采用 `./.agents/skills` canonical source
- 通过 `./.claude/skills` 软链接提供当前兼容层

## 16. 当前确认结论

- 默认目标：通用生成器
- demo 仓库：`~/git/semantic-router/main`
- 默认 coding 模式：子系统核心群画像
- 默认 review 模式：核心 maintainer 群画像
- maintainer 识别：纯行为识别
- review 样本目标：`100 个有效 review PR`，不足则全量
- coding 时间窗口：至少半年，子系统不足则全历史补齐
- 默认输出：`1 coding + 1 review`
- 复杂仓库可升级为多个 coding skill
- 指定模块时可只生成模块级 coding skill
- repo-local 路径：`./.agents/skills`
- 兼容路径：`./.claude/skills` 软链接
- 覆盖策略：强覆盖，但只限生成器管理的 skill
- 生成结果必须带详尽证据层
- 生成结果及其全部证据层内容统一使用英文

## 17. 仍待实现时细化的参数

这些不影响当前 spec 成立，但实现时需要进一步定量：

- “子系统样本不足”的阈值
- “复杂仓库需要拆多个 coding skill”的判定阈值
- 核心作者群识别的权重公式
- maintainer 行为识别的权重公式
- 证据层 JSON/Markdown 的最终 schema
- 生成器自身 skill 的触发语句和命令约定
