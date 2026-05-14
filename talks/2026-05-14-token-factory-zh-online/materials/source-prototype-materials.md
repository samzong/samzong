# Token Factory Source Prototype Materials

> 来源：`talks/2026-05-14-token-factory-zh-online/token-factory/`
> 用途：把老板下载的 Token Factory 原型源码整理成可复用素材，后续 PPT 和官网讨论优先基于本文，不反复读取源码。
> 注意：源码材料本身是内部讨论与 Mockup，不等于已发布产品能力；对外引用数据、客户、路线图和技术指标前必须再次核验。
> 重要补充：老板材料里的 `.html` 文件不是普通实现细节，很多就是 vibe coding 产出的最终可交互材料形态。Dashboard、Copilot、MaaS、架构蓝图等 `.html` 应作为原型成品和表达素材读取，而不是只看它们背后的 prompt 或 Markdown。

## 0. 已封存的重点 HTML 素材

以下文件已经把老板 HTML 原型中的可复用业务内容独立抽取出来，后续优先读取这些素材文件，而不是反复回到 HTML 源码：

- `HARD_GATES.md`
  - 位置：`talks/2026-05-14-token-factory-zh-online/HARD_GATES.md`
  - 作用：所有 PPT / 官网素材进入正式大纲前，必须先归类到 A/B/C/D 及细分场景，禁止发散和混淆。
- `materials/dashboard-html-materials.md`
  - 来源：`token-factory/dashboard/token-factory-dashboard.html`
  - 覆盖：Dashboard 页面结构、经营价值、业务经营、FinOps、安全、生产运营、资源成本、算电协同、模型-GPU 协同、指标口径、示例数据、经营建议。
- `materials/copilot-html-materials.md`
  - 来源：`token-factory/copilot/copilot-mockup.html`
  - 覆盖：Copilot 三栏工作台、多入口、输入区、右侧 Inspector、企业供给计划、运营分成设计、毛利归因、容量规划、OpenClaw RCA、老板摘要、桌面值班、模型路由、租户治理、数字人入口。
- `materials/inference-optimization-ppt-materials.md`
  - 来源：`推理优化PPTv0.1.0.pptx`
  - 覆盖：DaoCloud 推理优化技术先进性、InferX 生产闭环、Kubernetes + vLLM 技术壁垒、AI 网关、生产韧性、Planner、KV Cache、可观测闭环、五类硬件/模型优化案例。
- `sales-ppt-outline-v1.md`
  - 位置：`talks/2026-05-14-token-factory-zh-online/sales-ppt-outline-v1.md`
  - 覆盖：30 页高层销售拜访版 PPT v1 大纲，包含章节逻辑、每页对象/场景/结论/视觉建议/素材来源/禁止表达，供后续 vibe PPT 工具生产 PPT 使用。

## 1. 源码材料清单

### 1.1 总入口

- `README.md`
  - 定义该仓库是 DaoCloud Token Factory 的产品定义、架构蓝图与经营驾驶舱原型集合。
  - 明确“不包含后端代码”，交付物主要是 Markdown 研究文档、单文件 HTML 原型和静态部署配置。
- `sitemap.md`
  - 给出 `d.run` 的产品站点结构。
  - 核心路径：`/api`、`/console`、`/copilot`、`/management`。
- `index.html`
  - 静态入口页。

### 1.2 战略与产品定义

- `architecture/Token-Factory-2026-Product-Definition.md`
  - 产品定义、客户类型、业务模式、建设原则、典型业务用例、FAQ。
- `architecture/关于 DaoCloud Token Factory的讨论邀请.md`
  - 内部讨论邀请，强调 Token Factory 是 DaoCloud 下一阶段增长模式假设。
- `architecture/DaoCloud 未来 5-10 年产品计划的判断与建议（内部讨论稿）.md`
  - 公司 5-10 年产品重心迁移判断，提出 6.0、Token 使用层、Token 制造层、超节点层。
- `architecture/中国 Token Factory 市场规模研究.md`
  - 中国 Token 使用量、价格区间、市场规模和 DaoCloud 可行收入测算。
- `architecture/从 Linux 到 Kubernetes 再到 AI Factory OS：操作系统边界的三次上移.md`
  - 从 OS 边界上移解释 AI Factory OS / Token Factory 的行业位置。
- `architecture/roadmap.md`
  - 2026 年技术线和业务线 Roadmap。
- `architecture/token-factory-architecture.md`
  - 架构蓝图文字版。
- `architecture/token-factory-architecture.html`
  - 架构蓝图 HTML 版，是可交互架构表达材料，不只是代码实现。

### 1.3 产品原型

- `maas/index.html`
  - 一体化静态 HTML 原型，模拟 MaaS 前台、管理后台、容器管理、可观测四个平级系统；应按老板 vibe 出来的可交互产品材料读取。
- `maas/p.txt`
  - 生成 MaaS / 管理后台 / 容器 / 可观测原型的详细提示词和信息架构。
- `copilot/copilot-mockup.html`
  - Copilot 智能工作台原型，是 Copilot 当前最重要的可视化材料之一。
- `copilot/p.md`
  - Copilot 原型生成提示词和产品要求。
- `dashboard/token-factory-dashboard.html`
  - 经营驾驶舱 Mockup，是 Dashboard 当前最重要的可视化材料之一。

### 1.4 词库与辅助

- `mind/mind.md`
  - 名词大全，覆盖品牌、商业模式、云原生、AI 推理、硬件、市场、投资人、生态等术语。
- `package.json`
  - 仅包含 `sync:roadmap-feishu` 脚本。
- `scripts/*`
  - GitHub / GitLab / 飞书同步相关脚本。

## 2. 源码中的核心定位

源码中对 Token Factory 的核心定义：

- 不是单一推理平台。
- 不是模型服务上再套一层界面。
- 不是推理平台换名。
- 是把算力、模型、推理系统、缓存、调度、网关、计量、结算、运营组织成持续生产、交付和结算 Token 的系统能力。

源码里的高频表达：

- 把算力变成产能。
- 把 Token 变成收入。
- 把 GPU、网络、存储、模型、推理系统和流量组织成持续、稳定、低成本的生产体系。
- MaaS 是模型能力服务化的交付形态，不等于 ToC，也不只等于对外售卖；Token Factory 是背后的供给、经营与治理系统。
- 开源模型和推理引擎提供“可用能力”，但客户真正付费的是经营结果：稳定 Token 产能、更低单位成本、更好资源利用率、运营治理和交付保障。

可复用但需要讨论的主张：

> Token Factory 是把 GPU 资源转化为可售卖、可内部供给、可治理、可运营 Token 产能的系统。

与我们当前工作文档里的主张“GPU 资源变现的 MaaS 操作系统”方向一致，但源码更强调“生产系统 / 经营系统 / 中间控制层”。

## 3. 客户与业务模式素材

### 3.1 源码里的两类客户

源码将客户分为两类：

- 企业型客户
  - 中等体量。
  - 需求明确。
  - 愿意为持续 AI 能力付费。
  - 不愿自建过重的底层基础设施和供给体系。
  - 购买重点不是复杂平台，而是持续、稳定、可预期的 Token 供给能力。
- 运营型客户
  - 政府项目、国企资源、地方平台资源、产业合作客户。
  - 目标不是建设内部系统，而是建立 Token 供给与运营体系。
  - 关注资源如何组织、客户如何承接、收入如何分成、业务能否滚动。

与当前大纲映射：

- 我们定义的 B 类，是企业内部具体消费、管理和分析 Token 使用的组织 / 部门 / 员工视角，不一定是采购 Token Factory 的主体。
- 我们定义的 C 类，是 Token Factory 的采购与运营主体：地方智算中心是第一优先；大型企业如果建设内部 MaaS 供给平台，也属于 C 类。
- 当前销售 PPT 第一优先应服务 C 类，因此应优先采用“地方智算中心 / 地方平台资源 / 政府国资项目”的语境，同时保留“大型企业内部 MaaS 供给”的覆盖能力。

### 3.2 源码里的业务模式

企业型客户：

- 软件订阅。
- 软硬一体。
- 按年采购的持续供给服务。
- 更值得推演的是“持续供给型模式”：客户按年提出大致 Token 需求，由 DaoCloud 负责底层机器、资源组织、运行和调度，交付稳定 Token 供给结果。

运营型客户：

- 初装费 + 运维费 + Token 分成。
- 前期通过项目建设形成初始收入。
- 中期通过持续运维形成稳定服务收入。
- 后期通过 Token 运营和供给形成分成收入。
- 可通过合资公司或合作经营主体推进。
- 合作方负责客户拓展和项目滚动，DaoCloud 负责产品能力、系统组织和运营支撑。

这对当前销售版 PPT 的意义：

- 不应只讲“买一套软件”。
- 应讲“帮助地方智算中心建立可运营、可结算、可增长的 MaaS 生意”，同时讲清楚大型企业可以用同一套能力建设内部 MaaS 供给与治理平台。
- 对地方智算中心类 C，需要把交付模式、运营责任、计量口径、收入分成、样板项目讲清楚；对大型企业类 C，需要把内部供给、部门分账、预算、审计、应用接入和服务质量讲清楚。

## 4. 市场与规模素材

源码中的市场测算口径：

- 中国全国 Token 调用量：`140 万亿+/日`。
- 中国公有云对客 MaaS：
  - 2025H1：`2.97 万亿/日`。
  - 2025 预测：`5.48 万亿/日`。
- 中国市场工作价格区间：`1.5–2.5 元 / 百万 Token`。
- 全国 Token 价值等价市场：`766.5–1277.5 亿元/年`。
- 中国公有云对客 MaaS 市场：约 `30–50 亿元/年`。
- DaoCloud 中期可行收入测算：
  - 稳妥目标：`1.5–2.5 亿元/年`。
  - 做得好：`3–6 亿元/年`。
  - 合作伙伴铺开并形成网络效应：`6–10 亿元/年`。

源码给出的判断：

- 中国 Token 经济已经进入基础设施级需求阶段。
- 公众侧和企业侧是双轮驱动。
- 企业侧正在转向“开源为基座、闭源做增益”的混合格局。
- 模型 API 价格下降会压低纯模型溢价，但抬高部署、调度、缓存、网关、治理、运营系统的价值。
- 未来机会不只在模型本身，更在谁能把模型、算力、缓存、路由、观测和结算体系组织成低成本、高可用、可持续运营的 Token 生产系统。

对外使用注意：

- 这些数字来自源码中的内部研究稿，需要补公开来源和最新核验。
- 销售 PPT 可先作为“市场空间占位”，不要直接用作最终对外引用。

## 5. 产品系统信息架构素材

### 5.1 `d.run` 总体站点结构

源码中的 `d.run` 结构：

- `d.run/api`
  - OpenAI-Compatible API。
  - API Docs、Models、Endpoints、API Keys、Usage / Quota。
- `d.run/console`
  - MaaS 前台。
  - 模型广场、服务目录、Playground、API 接入、我的应用 / Workspaces、用量 / 配额、账单 / 套餐。
- `d.run/copilot`
  - 智能工作台。
  - Copilot、Agents、Workflows / Tools、AI 微应用、Dashboard、历史 / 上下文。
- `d.run/management`
  - 管理后台。
  - 总览、租户 / 工作区、模型与服务、配额 / 策略、用量 / 计费、审计 / 合规、集群、GPU / NPU、网络、存储、可观测、生命周期 / 运维。

### 5.2 MaaS 原型中的平级系统边界

`maas/p.txt` 和 `maas/index.html` 进一步把系统拆成六个平级系统：

- `d.run/api`：OpenAI-Compatible API 门户。
- `d.run/console`：MaaS 前台。
- `d.run/copilot`：智能工作台 / AI Copilot。
- `d.run/management`：Token Factory 管理后台。
- `d.run/container`：容器管理。
- `d.run/observability`：可观测。

关键边界：

- `console`、`management`、`container`、`observability` 是平级产品，不应混成一个左侧菜单。
- `container` 承接集群、GPU / NPU、网络、存储、生命周期 / 运维。
- `observability` 承接指标、日志、Trace、告警、根因分析。
- `Copilot` 是独立系统，但在 Console 和 Management 顶部需要有高可见度入口。

对官网和 PPT 的意义：

- 官网不宜只画一个“大后台”。
- 可以表达为“一个 MaaS 供给体系，需要 API 门户、MaaS 前台、管理后台、智能工作台、基础设施管理和可观测共同闭环”。对地方智算中心，它是对外经营闭环；对大型企业，它是内部治理与供给闭环。
- 销售 PPT 可以用这套架构解释 Token Factory 不只是 Token API，而是一套经营系统。

## 6. MaaS 前台素材

MaaS 前台面向：

- 普通用户。
- 开发者。
- 团队管理员。

左侧导航：

- 控制台。
- 调试场 / Playground。
- 模型目录 / Model Library。
- API 密钥。
- 接入点 / 部署。
- 批处理任务。
- 微调。
- 评测。
- 用量与账单。
- 团队 / 访问 / SSO。
- 日志 / 审计 / 支持。

重点能力：

- 今日 Token 用量、本月费用、活跃接入点、API Key 风险。
- 模型目录：DeepSeek-V3、DeepSeek-R1、Qwen2.5-72B-Instruct、GLM-4.5、Kimi-Latest、MiniMax-Text-01、SDXL、Flux、Embedding-Large。
- Playground：文本生成、图像生成、图像理解、Embedding；模型选择、参数配置、流式开关、响应结果、Token 用量、首字延迟、成本、请求 ID、代码示例。
- API Keys：Key 列表、Scope、最近使用、项目 / 工作区、风险状态、创建 / 删除 / 轮换 / 复制。
- Endpoints / Deployments：模型、模板、区域、扩缩容、健康状态、SLA、请求量、Token 用量、发布 / 暂停 / 回滚 / 日志。
- Usage & Billing：Token 用量趋势、按模型 / Endpoint 拆分、本月账单、配额进度、套餐、预警、账单导出。

对 B 类和 A 类的表达价值：

- A 类看到的是标准 API、模型目录、Playground 和应用接入。
- B 类看到的是企业内部用量、账单、团队权限、审计、配额和工作区管理。

## 7. 管理后台素材

管理后台面向：

- 平台管理员。
- IT 管理员。
- 治理团队。
- FinOps 团队。
- 安全团队。

源码明确要求管理后台信息层级：

> 经营优先、治理第二、技术靠后。

左侧导航：

- 总览。
- 租户 / 工作区。
- 模型与服务。
- 接入点 / API 网关。
- 配额 / 策略。
- 用量 / 计费 / 分账。
- 分析。
- 安全 / 审计 / 合规。

总览指标：

- 活跃租户。
- 活跃模型服务。
- 有效吞吐。
- SLA。
- 当日 Token 产出。
- 本月收入。
- 本月成本。
- 毛利率。
- 风险摘要。
- 最近治理 / 运维事件。

重点页面：

- 租户 / 工作区：生命周期、配额绑定、使用量、成本、RBAC。
- 模型与服务：模型上架 / 下架、发布服务、版本历史、服务模板、推理引擎绑定。
- 接入点 / API Gateway：路由、策略、限流、区域、灰度、健康、SLA、跳转可观测。
- 配额 / 策略：Token 配额、速率限制、优先级、SLA、成本保护、安全策略、Admission / Policy。
- 用量 / 计费 / 分账：总用量、按租户 / 部门 / 应用 / 模型拆分、Showback / Chargeback、预算预警、分账趋势。
- 分析中心：成本总览、Token 成本、模型成本、租户 / 客户成本、部门 / 工作区成本、Endpoint 成本、收入 / 毛利、预算 / 预测、优化建议。
- 安全 / 审计 / 合规：审计日志、调用审计、权限变更、策略命中、风险事件、合规摘要。

对 C 类的表达价值：

- 这不是技术后台，而是 C 类运营 Token 供给体系的管理控制面。
- 地方智算中心的 C 类运营人员看收入、成本、毛利、客户、套餐、分账；大型企业的 C 类平台负责人看内部消耗、部门预算、成本归因、合规审计、应用接入和服务质量。
- C 类运维人员通过管理后台进入容器管理和可观测，但管理后台本身不应该变成基础设施细节堆叠。

## 8. Dashboard / 经营驾驶舱素材

`README.md` 说经营驾驶舱围绕一次 Token 请求生命周期拆成 7 个驾驶舱：

- 经营价值。
- 业务经营。
- FinOps / 财务。
- 安全防护。
- 生产运营。
- 资源成本。
- 算电协同。

`dashboard/token-factory-dashboard.html` 中实际还出现了一个 `模型与 GPU 协同驾驶舱`，与生产运营里的模型 × GPU 协同内容有重复，需要后续确认是否算独立章节。

### 8.1 经营价值驾驶舱

核心表达：

- 不是在管理 GPU，而是在把算力、电力和安全控制协同转化为可交付、可盈利的 Token 产能。
- Token Factory 将异构资源组织为高效率生产系统，让每一份投入可度量、可归因、可优化。

可用指标：

- Token 产能。
- 收入。
- 毛利。
- 单位 Token 成本。
- GPU 有效利用率。
- 单位 Token 电耗。
- Value Attribution Bridge。
- With Token Factory vs Without Token Factory 基线增益对比。

### 8.2 业务经营驾驶舱

核心对象：

- 租户。
- 部门。
- 应用。
- Agent。

关注：

- Token 消费。
- 收入贡献。
- 增长分析。
- 业务对象 -> 模型 -> GPU -> Token 产出流向。

### 8.3 FinOps / 财务驾驶舱

面向 CFO / FinOps 团队。

关注：

- 收入。
- 成本。
- 毛利。
- 预算。
- ROI。
- 预测。
- 单机资产经营：每台机器是否赚钱、多久回本、是否值得扩容。
- Showback / Chargeback。

### 8.4 安全防护驾驶舱

关注：

- 风险识别。
- 拦截控制。
- 业务保护。
- 审计闭环。
- Prompt 注入、策略命中、异常租户、合规状态。

### 8.5 生产运营驾驶舱

关注：

- Token 生产实时控制。
- 请求、吞吐、延迟、缓存、模型 × GPU 协同调度。
- Token 吞吐、GPU 平均利用率、队列、TTFT、TPOT、SLA。
- 热点 GPU 池、故障、调度事件。

### 8.6 资源成本驾驶舱

关注：

- GPU 型号。
- 模型成本。
- 单卡产值。
- 空转与错配。
- 优化收益。
- GPU 型号成本效率排行。

### 8.7 算电协同驾驶舱

核心表达：

- 电力不仅是成本，更是 Token 产能的物理约束。
- 算电协同让功率限制从被动约束变成主动调度能力。
- 可讲绿电消纳、分时电价、PUE、功率上限、单位 Token 电耗。

对 PPT / 官网的意义：

- Dashboard 不只是“看板”，而是 C 类经营 Token 生意的驾驶系统。
- 它可以同时服务 C 类经营 / 治理、C 类运维、B 类企业使用管理和 D 类经营叙事。
- `dashboard/token-factory-dashboard.html` 已经包含老板 vibe coding 产出的完整 Dashboard 描述和界面代码，后续整理 PPT / 官网时应优先从该 HTML 抽视觉结构、模块名称、指标体系和示例数据。

## 9. Copilot 素材

Copilot 定位：

- `d.run/copilot` 独立智能工作台。
- 不是普通聊天机器人。
- 不是营销官网。
- 不是传统 SaaS 管理后台。
- 是面向运营、治理、FinOps、安全、容量决策的智能工作台。
- `copilot/copilot-mockup.html` 已经包含老板 vibe coding 产出的完整 Copilot 描述和界面代码，后续整理 PPT / 官网时应优先从该 HTML 抽交互入口、典型问题、对话样例、右侧工作记忆和动作闭环。

核心职责：

- 分析。
- 解释。
- 建议。
- 生成草案。
- 生成报告。
- 保持上下文。
- 联动仪表板、MaaS 前台和管理后台。

边界：

- 高风险结构性配置变更不直接在 Copilot 执行。
- Copilot 负责给出分析与建议，必要时引导“去管理后台执行”。

多入口：

- Web Console / 网页工作台。
- Mobile / 手机摘要。
- Voice / 语音会话。
- Digital Human / 数字人。
- OpenClaw / Custom Agent。
- OpenAI-Compatible API。

源码原型中的最近会话：

- 企业年度 Token 供给计划。
- 运营项目分成与结算设计。
- 毛利被压缩的原因分析。
- 今晚高峰容量方案。
- 给老板的今日经营摘要方案。
- 桌面值班工作台怎么组织。
- OpenClaw 异常根因分析。
- DeepSeek-R1 成本为什么上升。
- 数字人讲解入口。
- 是否应该调整模型路由。
- 哪个租户正在侵蚀 SLA。

代表问题：

- 今天毛利变差，主要是模型成本、租户结构，还是缓存命中率变化导致的？
- 当前哪个模型服务组合的单位 Token 成本最高？是否值得切换到其他路由策略？
- 如果今晚流量上涨 30%，哪个 GPU 池会先成为瓶颈？建议扩容、限流还是改路由？
- 哪些租户正在占用高价值产能，但没有带来相应收入或业务价值？
- 最近 TTFT 上升，是否与 KV Cache 命中率下降有关？
- 哪个部门本月 AI 预算超支最明显？
- 请生成一份给老板看的今日 AI 运营摘要，只保留最重要的 5 条结论。
- DeepSeek-R1 是否应该部分切流到 GLM-4.5，以提升 ROI？
- 当前有哪些风险正在影响可售产能，而不是只影响系统指标？

源码原型中的示例数值：

- SLA：`99.93%`。
- Goodput：`18.4M tok/min`。
- Token Cost：`¥1.82 / 1M tok`。
- Gross Margin：`34.7%`。
- Cache Hit Rate：`72%`。
- Queue Depth：`184`。

对销售材料的意义：

- Copilot 可以作为 Token Factory 的智能入口，而不是单独 AI 聊天功能。
- 对 B 类：问企业内部 Token 消耗、部门预算、项目费用、应用成本、报告生成。
- 对 C 类运营：问毛利、客户、套餐、流量、分成、营销、收入风险。
- 对 C 类运维：问 GPU 池、SLA、容量、TTFT、TPOT、KV Cache、路由和故障根因。

## 10. 架构素材

源码中的架构分层：

1. Token 使用层 / 企业 AI 使用层
   - 消费者与入口。
   - OpenAI-Compatible API、MaaS、企业 AI 应用、Agent / Copilot / Workflow、部门级 AI 使用。
2. 业务入口与服务交付层 / 服务入口与供给交付层
   - 把推理包装成可购买、可申请、可治理的服务。
   - MaaS 服务入口、API 网关、商业化与交易交付、经营分析、多租户编排、声明式模型服务、生态入口、安全接入。
3. Token 制造层
   - 第一视觉中心。
   - 分布式推理编排、智能调度、模型池、推理引擎、分层 KV Cache、Prefill / Decode 解耦、性能基准、控制闭环。
4. CloudNative AI 底座层
   - Kubernetes / 集群平台。
   - GPU / NPU 共享与异构调度。
   - AI 网络。
   - 存储与缓存底座。
   - 可观测 / 诊断。
   - 安全 / 租户 / 治理。
   - 交付 / 生命周期 / 产品化。
5. 算力与基础设施硬件层 / 平台扩展基础设施层
   - GPU / NPU。
   - 高速互联。
   - KV Cache 与存储承载。
   - 机房、电力、冷却。

源码中的关键边界：

- DaoCloud 供给边界：
  - 服务化封装。
  - 推理制造。
  - 资源调度。
  - 缓存体系。
  - 网络存储组织。
  - 治理、观测、生命周期与规模交付。
- 伙伴 / 客户供给边界：
  - GPU / NPU。
  - 互联网络。
  - 缓存与存储承载。
  - 电力、机柜、冷却、数据中心设施。

对 C 类的销售表达价值：

- 地方智算中心提供资源与场景，DaoCloud 提供把资源组织成 Token 产能和经营系统的中间控制层。
- 这能避免把 DaoCloud 讲成“硬件商”或“普通模型平台”。

## 11. 技术先进性素材

源码反复出现的技术关键词：

- Kubernetes。
- GPU / NPU 异构调度。
- HAMi。
- Kueue、Gang Scheduling、LWS。
- Gateway API Inference Extension。
- Higress、Knoway。
- vLLM、SGLang、Triton。
- Dynamo、LLM-D、ai-dynamo、Grove。
- KV Cache、LMCache、KVConnector、KVBM。
- Prefill / Decode 解耦。
- Goodput、TTFT、TPOT、ITL、SLA、Benchmark。
- RDMA、Underlay AI 网络、Spiderpool、Unifabric。
- 本地 NVMe、共享存储、Hwameistor。
- OpenTelemetry、SkyWalking。
- AICR、DRA、NVSentinel。

可整理成销售表达的技术维度：

- 推理性能：Goodput、TTFT、TPOT、吞吐、排队、尾延迟。
- 推理成本：单位 Token 成本、GPU 有效利用率、模型-GPU 匹配、KV Cache 命中率。
- 稳定性：SLA、故障切换、RCA、容量预测、自动扩缩、风险预警。
- 资源效率：异构 GPU / NPU 调度、GPU 共享、拓扑感知、训推混部。
- 交付能力：Kubernetes、标准化交付、私有化部署、一体机 / 超节点、生命周期管理。
- 运营能力：计量计费、配额、分账、预算、收入 / 毛利分析、客户洞察。

需要后续补真实案例：

- 硬件适配清单。
- 推理加速对比。
- 国产卡 / 异构资源验证。
- d.run 运营数据。
- 客户或项目中的稳定性、成本、利用率收益。

## 12. Roadmap 素材

源码中的 2026 锚点：

- 5-6 月
  - 运营版商业闭环跑通。
  - 计费 / 分账 / 网关 / 配额 / 首批付费客户。
  - 推理加速达到消费商水平。
  - 仪表盘 + Copilot 对内可演示。
- 6 月
  - 沐曦超节点发布。
- 7 月 WAIC
  - 仪表盘 GA 雏形。
  - Copilot 可演示。
  - 推理性能基准公开展示。
  - 企业版商业闭环跑通链路完整。
- Q3
  - 企业版商业闭环完善。
  - 运营版大规模复制启动。
  - 目标日产 `1 万亿 token`。
  - 仪表盘 / Copilot GA。
- Q4
  - 国产卡三标准达成。
  - 训推混部 GA。
  - SLA 闭环可证。
  - 运营版大规模复制进一步放大。
  - 商业模式 v1。

对外使用注意：

- Roadmap 明显是内部规划，不应未经确认直接放入官网。
- 销售 PPT 中可转化为“产品能力路线 / 共建路线”，但需要删去内部过强承诺和未确认时间点。

## 13. 当前素材与我们需求的关系

我们当前目标：

- 给市场团队准备 v1 讨论大纲和草稿。
- 最终输出销售拜访版 PPT。
- 最终输出全新官网。
- 第一优先服务地方智算中心，也就是当前最优先的 C 类；大型企业建设内部 MaaS 供给平台时也属于 C 类。
- 同时要解释 C 类如何服务 A 类和 B 类，从而获得收入。

源码材料可以提供：

- C 类销售主线：地方智算中心 / 地方平台资源 / 政府国资资源的对外经营闭环，以及大型企业内部 MaaS 供给与治理闭环。
- B 类价值主线：企业内部具体 Token 使用管理，包括部门 / 工作区、预算、分账、审计、Copilot、Dashboard。
- A 类体验主线：OpenAI-Compatible API、MaaS 前台、Playground、模型目录、API Key、Endpoint。
- D 类战略主线：DaoCloud 从软件平台走向 Token 生产与运营能力，打开第二增长极。

源码材料需要我们改造的地方：

- 源码里“6.0”叙事偏内部战略，不适合直接给客户看。
- 源码里企业型客户和运营型客户都很重；当前销售 PPT 应该优先服务 C 类地方智算中心，但不能把 MaaS 误讲成 ToC 或只对外售卖，大型企业内部供给也应作为可覆盖场景保留。
- 源码里技术和系统内容很丰富，但市场材料需要压缩成客户收益，不应堆术语。
- 源码里的 Dashboard 是大屏 / 驾驶舱风格，官网需要转成更清晰的模块价值。
- 源码里的数字和路线图都需要确认后才能对外。

## 14. 待确认问题

### 14.1 客户与叙事

- 当前 PPT 是否只聚焦地方智算中心，还是需要保留“大型企业内部 MaaS 供给”的独立章节或附录？
- “地方智算中心”对外是否可以明确说，还是需要用“地方算力平台 / 区域智算运营方 / 政府与国资算力平台”这种更宽泛表达？
- C 类采购方内部决策人是谁：主任 / 总经理 / 运营负责人 / 技术负责人 / 财务负责人 / 政府主管部门？
- 是否需要讲“合资公司 / 分成”这类商业合作方式，还是只讲产品能力和运营收益？

### 14.2 产品能力边界

- Dashboard 当前哪些能力已有，哪些是 Mockup，哪些是 Roadmap？
- Copilot 当前哪些能力已有，哪些只是交互原型？
- `d.run/console`、`d.run/management`、`d.run/container`、`d.run/observability` 是否都是 Token Factory 对外产品形态，还是只是原型中的抽象？
- OpenClaw、ClawOS、AgentOS、Hermes-Agent 哪些可以对外提，哪些只作为内部产品关系？

### 14.3 技术案例

- DaoCloud 作为 vLLM 核心贡献者企业的正式表述和证据是什么？
- 已验证的硬件适配有哪些：NVIDIA、昇腾、沐曦、H800、A100、L40S 等分别到什么程度？
- 推理加速对比数据能否按模型、硬件、场景给出？
- 是否已有单位 Token 成本、GPU 利用率、SLA、TTFT、TPOT、Goodput 的真实数据？
- 是否有 d.run 或客户场景可公开引用？

### 14.4 市场与官网

- 官网首屏是否继续讨论“GPU 资源变现的 MaaS 操作系统”？
- 官网是否需要分两个入口：地方智算中心对外经营 / 大型企业内部供给？
- 官网是否需要展示 Dashboard 和 Copilot 截图，还是先用能力模块表达？
- 官网是否强调“Token Factory 背后的 d.run 实践”？

### 14.5 销售 PPT

- PPT 是否采用“C 类采购逻辑优先，B/A 作为 C 的服务对象和价值验证对象”的结构？其中地方智算中心强调收入，大型企业强调内部效率和治理。
- 是否需要附录讲企业型客户，供销售遇到 B 类客户时使用？
- 是否需要单独一页讲“Token Factory 与 MaaS 的关系”？
- 是否需要单独一页讲“为什么地方智算中心现在需要这个”？

## 15. 可直接进入下一轮讨论的材料块

### 15.1 一句话候选

- Token Factory 帮助地方智算中心把 GPU 资源转化为可售卖、可计量、可运营的 MaaS 收入，也帮助大型企业把 GPU 和模型能力转化为可治理、可分账、可持续供给的内部 MaaS 能力。
- Token Factory 不是模型平台，而是 Token 生产、供给和经营系统。
- MaaS 是模型能力服务化出口，Token Factory 是背后的供给、经营与治理系统。
- 把算力变成产能，把 Token 变成收入。

### 15.2 三段式销售主线候选

1. C 类客户的核心矛盾：有 GPU 和模型资源，不等于有可持续的供给体系；地方智算中心缺的是收入闭环，大型企业缺的是内部治理闭环。
2. Token Factory 的核心能力：把算力、模型、推理、计量、计费、运营、治理组织成 MaaS 供给闭环。
3. DaoCloud 的可信理由：云原生平台能力、推理加速能力、d.run 运营实践、Dashboard / Copilot / MaaS 产品化能力。

### 15.3 Dashboard 价值候选

- 给经营者看收入、毛利、客户和产能。
- 给运营人员看用户、订单、套餐、分账和增长。
- 给运维人员看 GPU、模型服务、SLA、容量和故障。
- 给企业客户看部门、项目、应用、预算和费用归因。

### 15.4 Copilot 价值候选

- B 类问：哪个部门用量上涨，费用是否超预算，哪些 AI 应用值得推广？
- C 类运营问：为什么毛利下降，哪些客户侵蚀高价值产能，套餐是否需要调整？
- C 类运维问：哪个 GPU 池会成为瓶颈，TTFT 为什么上升，是否与 KV Cache 命中率有关？
- 管理层问：今天平台经营状况如何，风险是什么，下一步该做什么？

## 16. 后续处理建议

下一步不建议直接写官网或 PPT 成稿。更合理的顺序：

1. 先确认 C 类销售拜访版 PPT 的叙事顺序。
2. 再从本素材中挑选 PPT 页级素材。
3. 再把同一套叙事压缩成官网信息架构。
4. 最后才进入文案、视觉和页面原型。
