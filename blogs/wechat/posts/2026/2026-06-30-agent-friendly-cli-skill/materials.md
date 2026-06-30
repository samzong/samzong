# 素材笔记

这份笔记用于后续二改，不一定直接发布。

## 主判断

Lathe 和 kitup 的作用不是“再做两个工具”，而是降低 Agent 进入真实工程系统的摩擦。

更完整的表达：

```text
API contract
  -> generated CLI
  -> command catalog
  -> generated Skill
  -> safe installer
  -> agent host
  -> audited execution
```

## MCP / Skill / CLI 的层次

- MCP：开放协议，标准化应用如何给 LLM 提供上下文、工具和资源。
- Skill：把可复用的工作流、约束、示例和脚本打包给 Agent。
- CLI：真实业务系统的稳定操作入口，可测试、可审计、可进 CI。

这三者不是替代关系。

可复述为：

```text
MCP 解决连接。
Skill 解决认知。
CLI 解决可操作入口。
```

## Lathe 素材

Lathe 当前定位：

- 从 OpenAPI / Swagger / protobuf / GraphQL 生成 Cobra CLI。
- 生成 command catalog JSON、intent search、per-command detail JSON、auth metadata、request body builders、machine-readable output。
- 默认生成 `skills/<cli-name>/`。
- 推荐 Agent loop：
  - `<cli> search "<intent>" --json`
  - `<cli> commands show <path...> --json`
  - `<cli> commands schema --json`

架构素材：

- `lathe-architecture.png` 已从 `/Users/x/git/samzong/lathe/docs/images/architecture.png` 复制。
- 关键缝合点：`internal/generated/<module>/<module>_gen.go` 中的 `[]runtime.CommandSpec`。
- 生成期和运行期分离：codegen-time 处理 spec / overlay / render；runtime 处理 command tree / auth / request / output。

## kitup 素材

kitup 当前定位：

- shared installer SDK for bundled and public GitHub Agent Skills。
- producer-side installer，不是 marketplace，不是 registry。
- CLI 作者提供：
  - `appId`
  - `skillBundle`
  - `scope`
  - `agents`
- kitup 负责：
  - host detection
  - target selection
  - `SKILL.md` validation
  - copy / update / uninstall
  - `.kitup.json` ownership metadata
  - unsafe overwrite conflict
  - structured report

架构素材：

- `kitup-architecture.svg/png` 是本篇新画的图。
- host adapter DB 由 `spec/hosts.json` 驱动。
- 安全哲学：
  - files over services
  - data over branching code
  - copy over symlink
  - conflict over clobber
  - report over print

## OpenCLI 表述边界

不要拉踩。

推荐说法：

OpenCLI 方向很值得尊重。它在帮助已有 CLI、网站、桌面工具和存量能力变得更容易被人和 Agent 理解、描述和调用。Lathe 不是要否定这个方向，而是选择了更窄的 API-contract-first 路线：从 OpenAPI / Swagger / protobuf / GraphQL 生成长期可维护的 CLI + catalog + Skill。

官方/项目素材：

- opencli.org 当前标题是 `Specification | OpenCLI`，页面描述说这个 specification 目前是 proposal。
- jackwener/OpenCLI README 的定位是：`Convert any website into a CLI & run Browser Use on your logged-in Chrome`。
- 同一个 README 还说：把 websites、browser sessions、Electron apps、local tools 变成 deterministic interfaces for humans and AI agents。
- 它还提到可以作为 CLI hub，注册 `gh`、`docker` 等本地工具，也有 Electron app adapters。

所以更准确的说法是：

OpenCLI 更偏“连接和描述存量能力”，而不是只做一个简单包装器。它和 Lathe 的关系不是强弱，而是起点不同。OpenCLI 面向已有网站、浏览器会话、桌面和本地工具；Lathe 面向已有 API contract。

对比表达：

```text
OpenCLI 方向：已有能力怎么被稳定理解和调用？
Lathe：已有 API 产品怎么变成 Agent-ready CLI？
```

## 可引用链接

- Model Context Protocol: https://modelcontextprotocol.io/docs/getting-started/intro
- OpenAI Codex Agent Skills: https://developers.openai.com/codex/skills
- Anthropic Agent Skills: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- Lathe: https://github.com/lathe-cli/lathe
- Lathe architecture source: `/Users/x/git/samzong/lathe/docs/architecture.md`
- kitup: https://github.com/samzong/kitup
- kitup host adapter contract: `/Users/x/git/samzong/kitup/docs/host-adapter-contract.md`
- OpenCLI Specification: https://opencli.org/
- OpenCLI project: https://github.com/jackwener/opencli
