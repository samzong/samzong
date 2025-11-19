我需要编写一篇介绍提升算力效率的 PPT，我目前已经有了 6 个主题：

| 阶段                            | 关键技术手段                                        | 主要贡献                                             |
| ------------------------------- | --------------------------------------------------- | ---------------------------------------------------- |
| 基线                            | 传统裸金属租赁                                      | 初始低效利用，资源碎片化严重。                       |
| 阶段1：GPU共享与虚拟化          | GPU分片、NVIDIA MIG、时间共享、vGPU (HAMi)          | 解决轻量级任务独占GPU问题，提升单个GPU承载能力。     |
| 阶段2：智能工作负载编排         | binpack 调度策略、动态批处理、集群调度与公平控制器  | 最小化资源碎片化，最大化GPU利用，优化多租户效率。    |
| 阶段3：高性能数据基础设施       | RDMA网络、并行文件系统 (Lustre) 与GPUDirect Storage | 消除数据传输瓶颈，确保GPU持续获得数据。              |
| 阶段4：软件定义优化             | LLM推理加速 (PagedAttention, KV缓存复用、PD分离)    | 提升LLM推理吞吐量和训练效率，最大化每周期工作量。    |
| 阶段5：增强弹性与最小化停机时间 | 智能自动化弹性伸缩，异步检查点、容错训练框架        | 显著减少因故障导致的训练停机时间，提高有效计算时间。 |
| 阶段6：战略性工作负载管理       | “白天推理，夜间训练”、地理和时间优化                | 充分利用非高峰时段闲置容量，实现24/7持续高利用率。   |

## 技术背景

我是一家从事云原生 Kubernetes 的产品经理，目前主要的产品能力和技术关注点是，在 k8s 之上实现 GPU的高效管理、利用，同时支撑机器学习的模型训练，开发调度；已经大模型推理。

同时我在 GPU 的算力纳管能力已经提升到做大规模智算集群的纳管，包含 GPU 超节点纳管，智算中心需要的 RDMA 网络，高性能存储等，我们拥有这一系列的技术实力

## 目标

我现在需要撰写一份以上述六大阶段为主题的 PPT，主要用途是老婆对外 PR 宣讲，核心围绕的是我们通过这些技术手段如何如何提升了算力效率，主要做出了哪些贡献

## 输出

我现在需要一份大纲，只谈技术的硬核 PPT 大纲，至少需要每页的标题，并且涉及的技术点；我们内部已经有了非常多的材料，所以我只需要这个 PPT 的叙事结构和呈现思路，我自己去组装材料。

## 最后

我目前负责第二阶段的内容组装，在完成基础大纲后，帮助我完成第二阶段的详细内容组织。

## 其他

- 材料的需求方要求我们尽可能这些技术模块进行展开，按模块，把相应的技术填进去，写一份详细的ppt。
- 我的领导给了关于算电协同的建议，尤其是 CNCF Sustainability 中对于大模型推理额指标：
    Throughput (token/sec)
    Time-To-First-Token (TTFT)
    Time-Between-Tokens (TBT) 
    GPU utilization
    Memory overhead (GB) 
    Prefill efficiency (%)
    Decoding parallelism
    Cluster throughput per Watt
    还有个指标叫: Throughput/$ 可能更合适；Throughput/watt 是考虑能源的。
- 另外一个领导给出了 GPU Sharing 的好处: GPU Sharing / Right-Sizing
    Why: Smaller LLM models (SLM) can perform with a slice of a GPU
    Approach:
        Share GPUs across models with MIG partitioning or time-sharing (MPS)
        Right-sizing techniques to inform the size of the slice (analytic, or profiling based)