# llm-d 云原生的分布式推理

整个 PPT 的大概思路是：

1. 介绍大模型推理的重要性，以及为什么需要分布式推理？ 分布式推理的一些关键难题，引出来
2. vllm 当前的一些局限性，引出来 llm-d 的必要性，以及 为什么 K8s 是一个好的选择？
3. llm-d 的架构设计，以及一些关键技术点
4. 如何在你的产品引入 llm-d
5. llm-d 的后续发展
6. 如何参与 llm-d 的贡献 （开源代码仓库的结构）

---

**参考资料**：llm-d 官方架构文档与 `llm-d/llm-d` GitHub 仓库包含最新的组件清单、部署账本与 well-lit paths，v0.3（2025 年 10 月）升级进一步明确了 IGW、Scheduler 和 Wallet Paths 的状态。citeturn3search3turn1search5

## 大模型推理的发展

大模型推理已成为核心算力消耗环节。模型规模（参数量、KV Cache 体积）持续增长，GPU 内存成为瓶颈。
推理服务需同时满足高 QPS 与低延迟，但传统单体推理架构在资源利用率和灵活性上严重受限。

随着模型参数到达数百亿、甚至上千亿级别，单个请求需要跨多个时间步反复运行，TTFT/TPOT/TTLT 这类指标直接决定 SLO 是否达标。再加上用户会话的「状态感知」需求（KV Cache、prefix cache、长上下文），传统的 stateless 轮询调度已无法照顾缓存命中率与预填充代价，必须在更大的集群中做智能路由与资源分层。

## 为什么需要分布式推理（分体式推理）？

大模型推理的请求带有显式状态（KV Cache）和隐含缓存热度，长短不一的 prompt 造成负载分布极端不均。传统的 L7 load balancer 只会平等抛请求到不同节点，还会破坏缓存命中；而高并发下的 TTLT 与 TTFT 指标又对 SLO 产生了放大效应。分体式推理将 Prefill 和 Decode 拆分，配合缓存感知的调度器与路由，才能在多卡/多机上同时兼顾吞吐与尾延迟。

分布式方案还能结合自动扩缩、跨节点的缓存索引（如 LMCache/NIXL），把重复的上下文复用在同一台 Decode 机器上，避免每个请求都重新拉取 1000+ token 的 KV Cache，使得 GPU 资源可以用在真正的推理计算上。

## vllm 部署的一些局限性

vLLM 的设计是高效服务引擎，其关注点主要是单机或单节点多GPU环境“优化 KV 缓存”、“连续批理”“PagedAttention”。

当我们把它用于分布式／分体式推理时，会遇Prefill／Decode 拆分和调度、路由多节点、KV 缓存跨节点。

除此之外，实践中还会遇到镜像拉取、模型权重预热、Pod 冷启动等因素，导致 Horizontal Pod Autoscaler 对 LLM 完全失效（每个 Pod 拉模型需要几分钟，无法及时扩容）。vLLM 虽然在单机做到了 KV Cache 重用，但缺少聚合层去感知整体队列、前缀命中、硬件拓扑，无法对 “短 prompt 直接 decode、长 prompt 先 prefill” 这类策略做统一调度，也没有承担跨主机 multi-GPU/TPU 的同步。

## K8s 为什么是一个好的选择 ？

大规模 LLM 推理服务需要异构 GPU、缓存路由、请求形态识别与资源弹性扩缩，可监控扩缩与故障自愈，而这些正是 K8s 成熟具备的分布式调度系统的能力。同时 Kubernetes 内也拥有大量利用开源项目来支撑。

| 分体式推理需求                 | K8s 提供的能力                                                                         |
| ------------------------------ | -------------------------------------------------------------------------------------- |
| **Prefill / Decode 异构运行**  | Pod 模板与调度插件（Scheduler, Volcano, Kueue）支持按资源类型独立调度 GPU、CPU、TPU 等 |
| **跨节点 KV Cache 传输与通信** | 原生 CNI + RDMA / GPUDirect / Multus 支持高速互联                                      |
| **弹性伸缩与多租户隔离**       | HPA/VPA + Namespace/Quota 实现多租户的自动扩缩容与隔离                                 |
| **跨集群资源池化**             | Karmada / Cluster API 等支持多集群统一调度与灾备                                       |
| **统一运维与观测体系**         | Operator、Prometheus、Grafana、OpenTelemetry 等形成完整可观测闭环                      |
| **快速实验与灰度发布**         | 支持 Canary、蓝绿部署、滚动更新，方便验证新模型和新策略                                |

- 解耦与自治：Pod 是最小自治单元，天然支持分体式架构中的 Prefill / Decode 独立生命周期。
- 调度与弹性：通过 CRD/Controller 可以定义推理任务类型（如 prefilljob、decodejob）并按负载动态调度。
- 生态兼容性：与主流推理引擎（vLLM、Triton、TGI）无缝集成，可利用 GPU Operator、NCCL Topology、RDMA 网络栈。
- 云原生标准化：符合 OpenAPI、gRPC、Gateway API 标准，利于构建通用推理接口与混合云部署。

更重要的是，Kubernetes 已经拥有丰富的 Operator（GPU Operator、NVIDIA DCGM）、监控套件（Prometheus + Grafana + OpenTelemetry）以及多集群调度（Karmada/Cluster API），并且可以在 Gateway API 之上构建 endpoint-picker/route filter，使 llm-d 的调度与负载感知逻辑成为集群的第一公民，而非外部黑盒。

## llm-d 云原生的分布式推理

llm-d is an open-source, Kubernetes-native, accelerator-agnostic inference stack co-developed by IBM Research, Google, and Red Hat. It standardizes large-model (LLM) inference on open protocols and composable components, enabling scalable, cost-efficient serving across heterogeneous hardware.

核心原则是“调度、缓存、分离、SLO、可组合”，构建在 Gateway API + vLLM 的基础之上并引入：

- **Inference Gateway Extension（IGW）**，用来感知请求体、前缀缓存与分体式需求，而不是只看 HTTP header。
- **Inference Scheduler**，根据队列、KV 命中、模型加载状态动态调度 prefill/decode。
- **ModelService、InferencePool、EndpointPicker** 等 CRD，让任何推理引擎只要实现 inference-pool 协议就能被纳入调度。
- **KV Cache Manager（LMCache + NIXL RDMA）** 在节点间共享缓存，并通过 scoring plugin 让 routing sidecar 选出最合适的 Decode 机器。
- **Wallet Paths 与推荐实践**，提供 Helm/YAML + 基准数据的 “well-lit path”，帮助用户从 Day 1 到 Day 2 流程化落地。

## P/D Inference Scheduler

Kubernetes 原生调度器（Inference Scheduler）是在 Gateway API 上的调度层，作用是把每个请求按负载特征（队列长度、KV cache 命中、prompt 长度）送到最合适的 Prefill/Decode 实例，同时驱动 autoscaler 与 decode-sidecar。调度器支持：

- **Cache-aware routing**：对每个模型 Pod 维护 cache hit score，优先路由命中率高的节点。
- **Prefix cache scheduling**：通过 body-aware routing 把前缀相同的多轮会话，或者期待 long-context 的请求，送到同一组 Prefill/Decode 组合，以复用 KV state。
- **PD 分离阈值与指令**：可以配置当 prompt 超过某个 token 长度时强制走异步 Prefill → Decode；短 prompt 直接 skip Prefill，直接走 Decode。
- **Decode sidecar + scoring plugin**：decode pod 附带轻量 sidecar，负责监听 routing decision、触发 KV 订阅、向 Prefill worker 请求 KV chunk。
- **Autoscaling 结合 SLO**：根据 TTLT/TPOT/SLO 触发 Prefill 与 Decode 的 HPA，保证在高负载下仍维持 P99 延迟。

- 开源、Kubernetes 原生、兼容多种加速器的推理框架
- 明确且易用的推荐实践路径
- 可复现的基准测试
- 具备 LLM 感知能力的推理网关和自动扩缩容
- 遵循开放标准，具备高度可定制和可组合性

Kubernetes 原生调度器，负责协调 Prefill 与 Decode 流程。
基于推理 Pod 的指标，采用前缀缓存感知与负载感知的智能路由。
支持可配置阈值：当 prompt 长度超过预设限制时，自动触发远端 Prefill。
通过 decode-sidecar 代理实现请求的编排与路由。

该调度器的源码与插件由 `llm-d/llm-d-inference-scheduler` 仓库维护，EndpointPicker、filters、scoring 逻辑在官方架构文档中有详解。

推理任务调度器
通过 CRD/Controller 定义推理任务类型（如 prefilljob、decodejob）
按负载动态调度
与 K8s 调度器（Scheduler、Volcano、Kueue）集成

## Inference Gateway Extension（IGW）

IGW 是 llm-d 扩展 Gateway API 的组件，把 request-level routing 和 Prefill/Decode 调度能力拉到 API 层。它基于 Kubernetes SIG Gateway API Inference Extension 项目的 CRD，并在此之上注入 PD 与 KV cache 感知的插件。citeturn2search0turn2search6

它提供：

- **InferencePool / EndpointPicker CRD**：EndpointPicker 基于 cache hit score、queue depth、model state 等指标进行 body-aware routing，并与 ModelService 的 InferencePool 结合，为每个请求挑选最合适的 Prefill/Decode 组合。
- **Pipeline Filters**：可以读取请求中的 model_id、prefix、prompt 长度、session ID，动态决定是否走远端 Prefill（通过 `max_tokens=1` 触发 prefill-only call）、是否复用 prefix cache、是否采用 remote decode + KV transfer。
- **Decode-Sidecar Hooks**：IGW 结合 Routing Sidecar、Inference Scheduler 形成“prefill 完成 → KV chunk metadata 发布 → decode worker 调度”闭环，所有路由决策都可以沿 Gateway 绑在一起。
- **Observability + Wallet Paths**：IGW 会暴露 telemetry，让 Prometheus/Grafana 能直接把 routing/PD 指标纳入 SLO 监控，并配套 Wallet Path 的 benchmark/monitoring blueprints 进行验证。

IGW 让分布式推理的调度逻辑成为 Kubernetes 原生流量面，而不是外部黑盒。

## ModelService

ModelService 是 llm-d 的高层 CRD（配合 Gateway、InferencePool）用来定义一套 LLM 服务，从镜像、模型权重到硬件选择（GPU/TPU/CPU）都可以在 YAML 中声明，并且自动注入到 EndpointPicker 和 Autoscaler。常见的安装路径是通过 llm-d-infra 提供的 Helmfile（ModelService/InferencePool/IGW chart）生成 ModelService + InferencePool + Gateway，完成一键部署后即可触发分体式调度的全链路。llm-d-infra 也包括 ModelService Helm chart（2025.06.10 接受），所以文档/quickstart 都能从同一处获取组件定义。

ModelService 的当前实现已迁移至 `llm-d-incubation/llm-d-modelservice`（原 `llm-d/llm-d-model-service` 仓库于 2025 年 7 月 24 日归档），最新说明详见 llm-d.ai 的 ModelService 文档页。

## Routing Sidecar

Routing Sidecar 是与 Decode Pod 同部署的轻量代理，它在 Prefill/Decode 整个生命周期中负责：

- 接受来自 Inference Gateway Scheduler 的路由决策，维护 decode worker 的 KV chunk metadata。
- 在需要远端 Prefill 时充当桥梁，发送 `max_tokens=1` 触发 prefill；完成后把 KV transfer 结果同步到 decode 端，并流式返回首个 token。
- 在非 PD 模式下保持零开销，整体上让调度器感知的流量和实际的 token 生成保持一致。

Routing Sidecar 的源码在 `llm-d/llm-d-routing-sidecar` 仓库，llm-d 架构文档的 routing 章节描述了它与 Scheduler/IGW 的协作逻辑。

## KV Transfer (via NIXL Connector) KV-Cache Manager

跨节点 KV 转移通过 NIXL RDMA、LMCache、或 GPU-direct（NVLink/GPUDirect）完成，其核心原则是 **非阻塞**、**按需加载**、**预分配**：

- Prefill worker 在生成 KV cache 之后，立刻将 chunk metadata 用 scoring plugin 广播给调度器/sidecar，不再同步等待 decode 端 ack，避免了 blocking push 导致的 compute stranded。
- Decode worker 在收到 KV chunk id 后，采用非阻塞 pull 模式从 Prefill worker 拉取数据，也可以预分配内存（例如 Dynamo 方案）避免重复的 malloc。
- 当缓存命中时，routing 可以 skip Prefill，直接把请求送到持有最长前缀匹配的 Decode worker。
- 如果 KV cache 需要从 RAM/host offload 交换，llm-d 可以配合 GPU direct storage（WEKA/VAST）或 CPU offload 方案，把冷数据快速投回 GPU HBM。
- LMCache 官方文档展现了如何用 NIXL Connector 做 Prefill/Decode 之间的非阻塞 KV transfer，并与 llm-d 的 KV Cache Manager 集成。

## llm-d 的部署和体验 (llm-d-infra)

llm-d-deployer 于 2025 年 7 月 25 日被标记弃用，llm-d-infra 现在是所有部署文档的单一信源（2025 年 11 月最新状态）。citeturn3search6 llm-d-infra 的 quickstart 脚本（例如 GKE + L4/H100 GPU）会：

- 要求 Hugging Face Token 并在 `values.yaml` 中通过 `preset: basic` 等 Wallet Path 选项调整 context window、模型版本和缓存策略，以匹配你的 GPU 资源。
- 部署 NVIDIA GPU Operator、Gateway API/Inference Extension CRD、ModelService/InferencePool/Observability charts，这些都包含在 llm-d-infra Helmfile 中，可以按需启停。
- 启动 Prefill 与 Decode 实例（演示通常使用 Llama 3.2）；观察请求在 Gateway → EndpointPicker → Routing Sidecar → vLLM 之间的完整流动，整个管线由 llm-d-infra 的 YAML/Helm 模块管理。
- 快速入门步骤、Helmfile 设置与 Wallet Paths 说明都记录在 llm-d-infra 的 Quickstart 文档中。
- 默认联动 Prometheus+Grafana 监控，Wallet Paths 里内置 benchmark/monitoring blueprint 方便验证 routing、KV cache 命中率与 PD SLO。

llm-d-infra 的设计倾向于组合化：你可以只部署 GIE、InferencePool、ModelService chart（该 chart 于 2025 年 6 月 10 日获准接受）或 LeaderWorkerSet 组件，无需再依赖单一的 llm-d-deployer chart。这样可以根据团队硬件（例如 H200、TPU、Intel XPU）灵活选配组件，并保持与 llm-d 社区的最新实践同步。

## llm-d 部署 MoE

在 MoE 场景（如 DeepSeek R1）中，llm-d 把 Prefill/Decode 再细分成专家并行（TP/PP）与 KV cache 级别的调度。通过 wallet paths 预先配置不同的 expert/route + NIXL 的跨 host 传输，每个 decode pod 只需要拉取自己负责的专家（sparse expert）上下文，就能把算力与显存压力限制在线上，并且在 PD 分离的套路下自然做到不同硬件（如 TPUs run Prefill、GPU run Decode）的协同。

## llm-d 部署 Deepseek R1

DeepSeek-685B/DeepSeek R1 这类 >1TB 模型需要 multi-host inference。llm-d 的规划中提到了 LeaderWorkerSet API：一个 leader pods 协调多个 worker pods（每个 worker 可持有不同 TP/PP 拓扑），通过在 Gateway 层做 endpoint picker, 同时利用 NIXL/LMCache 让每个 worker 只拉取其负责的 KV chunk，支持跨节点的拼接与 GPU direct 通信，避免了之前必须把所有参数 load 到单个节点的限制。

## llm-d 的版本更新 v0.3

v0.3 release on May 20, 2025 brought the Inference Gateway (IGW) 1.0 GA, wider hardware support (Intel XPU、Google TPU)、TCP + RDMA over RoCE 的 disaggregation 测试以及 predicted latency balancing 预览，这些改进让集群在 long-prefill workload 上可把 P90 延迟降低 3× 以上，还把 DeepSeek Expert Parallel（EP）推向 2.2k tokens/s/H200。与 0.2 相比，社区把更多 well-lit path 绑在一起，整合 handle 性能、调度、模型一致性与监控，持续扩大可以直接复用的部署蓝图。citeturn3search6

## llm-d-incubation/workload-variant-autoscaler（WVA）

WVA 是 llm-d-incubation 推出的 Kubernetes controller，用来实现 llm-d Architecture 中提出的 Variant Autoscaling over Hardware, Workload, and Traffic：它从 VariantAutoscaling CR 与 vLLM 实例中收集 metrics，估算每个 variant 符合 SLO 的 ITL/TTFT 目标，并跑一个 global optimizer 找出最省钱的 replica/GPU/批量组合，同时通过 Actuator 把 promotion metrics 暴露给 HPA/KEDA。citeturn0search0turn0search7

- **架构与流程**：Northstar 设计描述了 Collector/Model Analyzer/Optimizer/Actuator 等模块依次采集 telemetry、建立负载模型、求解全局 allocation、并把结果写回 VariantAutoscaling status 与 Prometheus，使得 Prefill、Decode、latency-sensitive 与 throughput-oriented 请求都能被统一调度。citeturn0search0turn0search3
- **建模与优化**：该 autoscaler 会衡量每个 model server 的容量、衍生考虑 request shapes 与 QoS 的 load function，并根据最近的 traffic mix（QPS、QoS、shape distribution）反复求解最省钱的 instance mix，目的是让 HPA 在不同阶段正确匹配所需的硬件。citeturn0search0turn0search4
- **运营及可观测性**：实践建议在模型 warm up 后再创建 VariantAutoscaling CR，使 WVA 能持续更新 status、写入 desired allocation、对外报告 load metrics，借助 HPA/KEDA 的响应把 pods 拉成与实际 SLO 需求匹配的数量。citeturn0search0turn0search3
- **价值与方向**：WVA 引入 GPU-aware autoscaling、multi-model prioritization 与 cost-aware planning，让繁杂的 accelerator 池能优先满足高关键度工作、提高延迟可预测性，并对实际硬件/流量条件保持部署安全。citeturn0search0turn0search5

## llm-d 的贡献参与（仓库和孵化）

### llm-d

**描述**：核心组织，包含所有走向生产环境关键路径的代码。

**规则**：

- 遵循 API 变更与废弃（Deprecation）流程
- 所有重大变更需提交项目提案（Project Proposal）
- 如后续需要中间层仓库（midstream repos），会在本组织内纳入管理

### llm-d-incubation

**描述**：所有实验性或尚未完全支持的组件。

**目的**：

- 将 llm-d 组织内的代码范围限定为最小可用项目（Minimum Viable Project）
- 为实验与孵化项目提供更低门槛、更灵活的场所

**规则**：

- 鼓励实验，只要每个组件有明确的目标与意义
- 每个仓库必须包含一个 README，简要说明目的与目标
- 毕业（成熟）的组件会迁移至 llm-d 组织

## llm-d 的后续发展

v0.3 stabilizes today’s well-lit paths，但社区已经在打磨下一代路线：

- **预测延迟调度**：实验性的 scoring predictor 已引入 prompt 长度、在飞 tokens、并发量等特征，预判 TTFT/TPOT 以在 25%-75% 衰减窗口内完成负载平衡。
- **Native CPU offload**：vLLM 正在复用 async KV transfer API，让冷 KV cache 可以 spill 到 CPU，并由调度器通过 KV event 感知何时拉回 GPU。
- **更多硬件与拓扑**：继续扩展 GPU/CPU/TPU/Intel XPU + wide expert parallel 的 well-lit path，并测试 TCP + RDMA over RoCE 的 disaggregation，确保 multi-host DeepSeek 等超大模型有明确路线图。
- **长期观测与基准**：为 PD、路由、缓存命中引入可复现的 benchmark/monitoring blueprints（Wallet Paths），让每次版本升级都有数据可查。
