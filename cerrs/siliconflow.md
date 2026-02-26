# 硅基流动 (SiliconFlow) 私有云 MaaS 产品技术调研报告

## 导言

硅基流动（SiliconFlow）已从 API 聚合商转型为企业级 MaaS 基础设施服务商，具备软硬协同设计能力。对竞品产研团队来说，需要关注的不是"极速推理"之类的商业口号，而是几个具体的技术方向：针对 MoE 模型的分布式推理架构、底层算子融合、开源与企业版双轨制，以及多模态管线的云端卸载策略。

本报告基于开源代码提交记录、学术论文、专利申请、开发者社区反馈和 API 接口设计，尝试剥离官方包装，还原硅基流动的底层技术细节。重点关注其与华为昇腾体系的联合调优，为竞品团队提供计算资源解耦、算子开发、高并发调度和私有云交付方面的参考。

## 私有云 MaaS 底层架构：PDC 解耦与统一总线网络

千亿至万亿参数的大语言模型（尤其是 DeepSeek-V3/R1 等具备 MLA 机制的模型），传统单节点或标准 RDMA 集群架构在计算密度、内存带宽和芯片间通信上都会碰到瓶颈 [1]。vLLM 的 PagedAttention 或 TensorRT-LLM 的原生调度将 Prefill 和 Decode 耦合在同一张卡上，但 Prefill 是计算密集型，Decode 是内存带宽密集型。两者挤在一起，资源碎片化严重，吞吐量上不去。

### PDC 资源解耦架构

硅基流动在私有云中引入了 PDC 架构（Prefill-Decode-Caching Disaggregation），基于点对点通信，将推理工作流拆成三个可独立扩展的子系统 [1]。

预填充集群（Prefill Cluster）由专门优化 GEMM 的 NPU 构成，只负责处理输入 Prompt、生成首个 Token、构建初始 KV Cache [1]。剥离解码任务后，计算单元能保持高负载运转。

解码集群（Decode Cluster）的调度策略优化为低延迟内存读取模式 [1]，通过自回归方式逐个生成后续 Token。解码节点持续从缓存层拉取和更新状态，核心需求是内存带宽而非矩阵算力。

分布式缓存集群（Caching Cluster）依托统一总线（UB）网络，构建了物理分布但逻辑统一、可全局寻址的内存池 [1]。它有两个用途：上下文缓存（存储多轮对话的 KV Cache 以供复用，降低 TTFT）和模型缓存（预加载高频模型权重，消除多租户场景下切换模型的冷启动延迟）[1]。

PDC 架构下，解码节点不再绑定特定的预填充节点，二者通过 KV Cache 传输接口异步交互。系统可按流量特征弹性伸缩——长文本分析时扩 Prefill 集群，高频短对话时扩 Decode 集群 [1]。

### 统一总线网络（UB-Mesh）与超级节点拓扑

PDC 架构成立的前提是底层适配了华为 CloudMatrix384 的 UB 网络 [3]。CloudMatrix384 作为超级节点，单集群内集成 384 张 Ascend 910C NPU 和 192 张 Kunpeng CPU [3]。

传统集群跨节点通信依赖 VPC 或标准 RDMA，传输数百 GB 的 KV Cache 时延迟突刺明显。硅基流动直接用 UB 协议绕过传统网络栈，在 384 张 NPU 间建立全互联直通通道 [3]。

测试数据：跨节点带宽衰减控制在 3% 以下，通信延迟增加不到 1 µs [3]。大语言模型推理对带宽敏感但对微秒级延迟不太敏感，所以这点开销基本可以忽略。效果上，整个物理集群在逻辑上被抹平，像一张巨大的"单卡"一样跑推理负载 [3]。

### 大规模专家并行（LEP）

MoE 架构（如 DeepSeek-R1 的 256 个路由专家）用传统的 TP/DP 策略处理稀疏激活时，通信开销和负载不均问题突出。硅基流动在 Decode 集群中引入了大规模专家并行（LEP）[1]。

私有云平台最高支持 EP320 并行度 [3]。系统通过 UB 网络派发 Token 并聚合专家输出，将 320 个计算逻辑分别映射到 320 个独立 NPU Die 上。

在解码阶段，每个 NPU Die 的 HBM 中只驻留一个专家的权重 [2]。这种"一芯一专家"的物理隔离消除了多专家共驻时频繁的内存页面置换和上下文切换开销，对解码延迟的改善很显著。

## 推理引擎：算子融合与调度机制

PDC 和 UB 网络是宏观基础设施层面的改进。微观层面的算子融合和显存管理，才是其高吞吐和低成本承诺的技术支撑 [5]。Python 层的调度优化已经接近天花板，C++/CUDA/CANN 级别的算子融合才是下一步的重点。

### MLAProlog 与算子融合

大语言模型推理中一个容易被忽略的性能瓶颈是大量小算子频繁启动带来的 Kernel Launch 开销。成千上万个 Token 的生成过程中，这些开销累积起来很可观。硅基流动的推理引擎用 MLAProlog 复合算子来解决这个问题 [1]。

MLAProlog 把注意力机制计算前的准备步骤合并成一个执行体：RMSNorm 归一化、Q/K/V 线性投影、RoPE 位置编码 [1]。原本需要多次 Kernel 启动的计算变成一次指令下发。

MLAProlog 内部还做了异构核心微并行调度：子任务拆解后以流水线形式跨 AIC（矩阵计算单元）和 AIV（向量计算单元）同步执行。向量归一化和矩阵投影的计算时间互相掩盖 [1]。

MLA 计算阶段同样做了融合注意力（FA）优化。在 FlashAttention 基础上，把 Concat 和 Slice 等数据塑形操作融入 FA 算子内部，提高数据局部性——数据读入 SRAM 后完成所有运算再写回 HBM，减少不必要的数据搬运 [1]。

### 显存布局：从 BNSD 到 BSND

多 Token 预测（MTP）和大规模批量并发场景下，传统 BNSD（Batch, Number of heads, Sequence, Dimension）布局容易导致计算核心负载不均。

硅基流动转向 BSND（Batch, Sequence, Number of heads, Dimension）布局 [1]，沿 B 和 S 轴做自适应切片。因为模型的注意力头数（N）和头维度（D）在推理时固定不变，沿 B/S 轴切片能保证子任务数据块大小均匀，负载均衡好，消除尾部延迟突刺 [1]。

另一个优化是 NZ-Formatted KV Cache。传统框架以 ND 格式存储张量，但硬件矩阵加速器需要 NZ 排布，每次计算前后都要做格式转换。硅基流动调用 NPU 的即时转换接口，生成 KV Cache 时直接以 NZ 格式写入，省掉格式转换开销 [1]。

配合微批次流水线调度，Prefill 和 Decode 任务被切成更小的时间片，在不同计算单元上重叠执行，避免管线停顿 [1]。

### INT8 量化

私有云部署中显存容量直接影响 TCO。硅基流动集成了权重和激活值的双向 INT8 量化 [2]。

这里的 INT8 量化不同于开源社区常见的粗糙方案（早期 AWQ/GPTQ 往往牺牲推理质量）。依托 Ascend 910C 的低精度硬件加速指令集，该方案在压缩显存占用的同时，在 16 个基准测试集上保持了与 BF16/FP16 近乎一致的精度 [2]。

这让单卡能释放更多显存给 KV Cache，直接提高并发处理上限 [2]。

| 优化维度 | 实现路径 | 解决的问题 | 产研启示 |
| --- | --- | --- | --- |
| 算子调度 | MLAProlog 复合算子 + Fused Attention，AIC-AIV 流水线并行 [1] | 小算子 Kernel Launch 开销和数据搬运延迟 | Python 层优化接近天花板，C++/CUDA/CANN 级算子融合是下一步 |
| 显存排布 | BSND 布局，沿 B/S 轴自适应切片 [1] | MTP 场景负载不均和尾部延迟 | 需要针对模型注意力机制动态调整内存步长 |
| 数据传输 | 硬件接口直接生成 NZ-Formatted KV Cache [1] | ND→NZ 格式转换的带宽浪费 | 调用硬件原生即时转换接口，避免不必要的显存拷贝 |
| 量化推理 | 硬件级 INT8 权重与激活双量化 [2] | 显存不足限制并发 | 私有云交付中量化精度直接影响客户 TCO 决策 |

## 多模态与图像生成：OneDiff 双轨制架构

多模态能力（图像和视频生成）是硅基流动吸引电商、游戏和广告客户的重要卖点。开源项目 OneDiff 是这块业务的基础，但它的商业策略值得单独分析。

### 社区版与企业版的分界

OneDiff 是 GitHub 上开源的扩散模型加速库（2000+ Star），通过接管 diffusers 和 ComfyUI 实现底层优化 [7]。但社区版和企业版之间有明确的功能分界。

社区版提供基础加速：支持动态分辨率、LoRA 热切换、SVD 约 2.0x 加速 [10]。主要靠图重写和算子替换，够用于低并发场景。

企业版需要购买 License [12]，提供三项关键优化：

1. 针对 SDXL、SVD 等高频模型的深度计算图融合，在社区版基础上再提升 20%~100% [10]
2. Int8 量化引擎：针对去噪 U-Net/DiT Transformer 块的无画质损耗量化方案，通过精确的缩放因子校准，让大模型能跑在显存更小的卡上 [10]
3. DeepCache 集成：利用相邻时间步特征图的冗余性跳过重复计算，SVD 任务最高达 3.9x 加速 [10]

### 编译器后端演进：OneFlow → Nexfort

OneDiff 的后端经历了明确的更迭。早期绑定 OneFlow 框架做静态图优化 [8]，针对 CUDA 11.8/12.1/12.2 环境发布预编译扩展包。

随着模型架构从 U-Net 转向 DiT（FLUX、SD3、PixArt），以及算力转向 H100 Hopper 架构，OneFlow 的优势减弱。硅基流动开始向 Nexfort 引擎过渡 [8]。官方指南已明确：DiT 模型或 H100 上的推理任务应使用 Nexfort [8]。

| 功能 | 社区版 | 企业版 | 差异分析 |
| --- | --- | --- | --- |
| 图/文生成加速 | 相对开源框架 2x [10] | 再提升 20%~100% [13] | 社区版拉用户，企业版赚钱 |
| SVD 速度 | 约 2.0x [10] | 结合 DeepCache 达 3.9x [10] | DeepCache 是高溢价功能 |
| 量化 | 不支持 | Int8 无损在线/离线量化 [10] | 显存压缩能力是核心商业壁垒 |
| 技术支持 | 社区论坛 [13] | 一对一专家支持 [13] | 私有云 MaaS 卖的是服务，不只是软件 |
| 动态切换 | 动态分辨率 + 毫秒级 LoRA 切换 [8] | 端到端企业级工作流加速 [8] | 对上层应用透明 |

## 开源生态与边缘计算卸载

硅基流动通过开源工具链把边缘计算需求引导到私有云集群。

### BizyAir：Serverless 多模态卸载

BizyAir（800+ Star）是为 ComfyUI 定制的 Serverless 节点集合 [16]。解决的问题很直接：企业内部设计师和运营人员需要在没有 GPU 的办公电脑上跑 FLUX.1-dev、Hunyuan3D 等大模型。

BizyAir 在本地执行轻量节点逻辑，把生成、预处理（ControlNet 深度/边缘提取）、后处理（超分辨率）等重活通过加密传输路由到云端 GPU 资源池执行 [16]。

工具集包括 JoyCaption（图像打标）、SAM（图像分割），以及 BizyBot——一个基于 VLM/LLM 的辅助工具，用户可以通过文本对话直接修改 ComfyUI 的图像输出 [16]。

### 企业级客户端：ChatGPT-Next-Web 定制版

硅基流动 Fork 了 NextChat（ChatGPT-Next-Web）做企业定制 [16]。主要改动集中在合规和权限方面：集成 MCP 协议让模型安全访问企业本地文件系统和数据库；内置管理员控制台做资源分配和租户权限管控；加入数据安全审查模块，自动拦截敏感查询，提供对话记录的全链路追踪和审计 [16]。

### 压力测试工具：llm-stress-testing

Go 语言编写的高并发压力测试工具 [16]，利用 Goroutine 的低开销特性，单机可模拟 100 万持久连接（HTTP/1.1、HTTP/2.0、gRPC、WebSocket），支持超过 10,000 QPS，100 并发用户下维持约 18,336 QPS [16]。

相比 Apache ab 之类的传统工具，它针对 LLM 流式输出做了适配：实时刷新耗时/并发/成功率/延迟指标，支持自定义文件输入（@filename 语法）模拟不同长度的 Prompt，生成可视化 HTML 报告辅助定位内存泄漏或线程锁死 [16]。对企业客户来说，这也是验证 SLA 的工具。

## 性能基准测试

### CloudMatrix384 上的 671B 模型

2025 年 6 月的技术评测报告显示，硅基流动与华为合作，用 CloudMatrix-Infer 引擎在 CloudMatrix384（Ascend 910C 集群）上跑通了 DeepSeek-R1（671B 参数）。

经过微批次流水线、INT8 双量化和 EP320 专家并行优化后的数据：

- Prefill 吞吐：单 NPU 达 6,688 tokens/s [1]
- Decode 吞吐：1,943 tokens/s per NPU，TPOT 控制在 50ms 以内 [1]。Batch Size 96 的高并发环境下，计算效率 1.29 tokens/s/TFLOPS [1]
- 严格延迟约束（15ms TPOT）下仍维持 538 tokens/s per NPU [1]

集群资源利用率方面：BF16/FP16 计算密集型场景录得 65.4% 理论峰值利用率；内存带宽密集型任务达 84.1% 内存带宽利用率 [1]。这组数据说明经过算法优化和编译重构，非 NVIDIA 硬件也能跑出不错的大模型推理性能。

### 与主流框架横向对比

| 评估维度 | vLLM | TensorRT-LLM | Fireworks AI | SiliconFlow |
| --- | --- | --- | --- | --- |
| 吞吐与延迟 | 吞吐高出未调优 TRT-LLM 约 70%-80%，延迟低 40% [19] | 延迟低但需要预编译，环境适配繁琐 | 优化 Float4 与内核，大批量路由模型吞吐高 [20] | 相比通用云平台基线，推理速度最高提升 2.3 倍，延迟降低 32% [21] |
| 并发扩展 | PagedAttention 在高并发下吞吐曲线平滑 [19] | 受显存碎片化和静态批处理限制，容易出现性能断崖 [23] | 定制连续批处理和 KV Cache 分片 [20] | 基于 UB 全局分布式缓存和 PDC 架构，可线性横向扩展 |
| 生态兼容 | OSS 优先，兼容 Hugging Face 和各类 CUDA 显卡 [23] | 绑定 NVIDIA 特定架构，落地门槛高 [23] | 面向 Blackwell 优化，也提供 VPC 部署 [20] | 兼容主流开源格式，擅长对接昇腾等国产算力 [22] |

整体来看，硅基流动在 TTFT 和序列生成方面有优势。但需要注意：在纯 NVIDIA H100 环境下，针对 CUDA 深度优化的闭源方案（如 Fireworks AI 的 FireAttention）在单节点峰值上可能更好 [24]。硅基流动的优势更多体现在异构的、有成本和隐私约束的企业内网场景。

## 企业级 API 与云原生交付

### OpenAI 兼容 API

硅基流动全面兼容 OpenAI API 规范 [25]。已经集成 LangChain、LlamaIndex 或 OpenAI SDK 的企业开发团队，迁移时只需改 base_url 和 api_key [26]。迁移成本低是撬动企业客户的关键。

平台也提供 gRPC 接口，用于对传输开销敏感的微服务场景，避免 HTTP/REST 文本解析的额外开销 [16]。

### 高阶 API 能力

- 结构化输出与 JSON Schema 校验：模型输出严格符合 JSON 规范，底层做 Schema 对齐，替代正则解析 [27]
- 前缀补全与 FIM（Fill-In-the-Middle）：同时提供代码上下文，让模型填补中间部分。是构建编程助手的基础 API [27]
- Function Calling 与交错思考（Interleaved Thinking）：模型可主动调用外部系统（ERP、实时汇率接口等），结合多模态处理形成 Agent 链路 [5]

### BYOC 交付与数据隔离

面向金融、政务等对数据主权敏感的客户，硅基流动提供 BYOC（Bring Your Own Cloud）私有化方案 [5]。

整套 PDC 架构和加速引擎封装为 Kubernetes Operator [28]，可接入企业现有 K8s 集群。多租户环境下实施计算、网络和存储三重隔离 [5]。按隐私协议，用户数据所有权归用户，硅基流动不得用于训练公共模型 [22]。系统还支持异构 GPU 整合调度和多集群容灾切换 [6]。

## 专利分析

查看 CNIPA 的专利申请可以推测其技术方向。

### 专利一：稀疏 LLM 数据并行处理

CN120276850A（2025 年 3 月申请）：《基于 MLA 的稀疏 LLM 的数据并行处理系统及方法》[30]。

时间和技术方向与 CloudMatrix-Infer 架构对 DeepSeek V3/R1 的优化吻合。这项专利大概率保护的是 EP320 大规模专家并行的底层路由逻辑——在多节点集群中如何用 UB 协议对稀疏 Token 做切片和重组分发，如何在计算核心间建立动态映射（结合 BSND 布局），消除稀疏路由带来的计算核心空转和显存碎片化。

### 专利二：基于 LLM 的交互式图像处理

CN119806714A（2025 年 1 月申请）：《基于大语言模型的交互式图像处理方法及装置》[31]。

申请时间早于 BizyAir/BizyBot 的功能发布。该专利跳出了传统的"提示词生图"路径，方向是让微调过的 LLM 解析用户的自然语言指令，自动转译为约束条件（ControlNet 参数、区域重绘蒙版、LoRA 权重切换），再交给 OneDiff 加速的扩散引擎渲染。本质上是 LLM 做意图理解，扩散模型做渲染执行。

## 社区争议与产品痛点

### OneDiff 双轨制的争议

社区版和企业版的功能分界引发了不满 [32]。社区版提供 2.0x 加速 [10]，但 Int8 量化、DeepCache 联合优化（3.9x）、针对高频模型的编译器深度优化都锁在企业版中 [10]。Reddit 上有开发者批评这种做法：用开源吸引用户，但把关键性能组件闭源，限制了社区对底层技术的二次创新 [32]。

### "Token 关税"问题

社区中有人用"Token 关税"来形容这个现象 [33]：硅基流动接入上百种模型，各模型的 Tokenizer 不同（BPE vs SentencePiece），同一段文本在不同平台上计算出的 Token 数量不一样。有开发者反映，相同文本在硅基流动平台上比其他服务商多计费约 25% [33]。对日处理大量 Agent 请求、成本敏感的商业项目来说，这种计费不一致是个实际问题。

### K8s 部署门槛和硬件锁定

两个落地层面的问题：

一是部署太重。不像 vLLM 一条 Docker 命令就能跑起来，硅基流动的完整架构依赖 K8s Operator 编排 [29]。中小企业做 PoC 验证时，部署成本和试错门槛偏高，缺少轻量级的试用入口。

二是硬件锁定隐忧。那些最亮眼的性能数据（单卡 1,943 tokens/s 解码、近乎无损 INT8）几乎都是在华为 Ascend + CANN 软件栈上取得的 [1]。在 NVIDIA H100 等主流 CUDA 环境中，这些自研算子（如 Nexfort 编译器生成的优化内核）能否复现同等性能，目前缺少公开数据 [34]。对正在选型的企业来说，这是一个实际的顾虑。

### 长上下文场景的 K 矩阵瓶颈

即便有 PDC 和 UB 网络，处理超长上下文（整本财报分析、大型代码库问答）时，K 矩阵的加载和搬运仍然是瓶颈 [35]。团队尝试了 L1 Cache 映射重分配和滑动窗口 K 矩阵驻留机制来掩盖访存延迟，但在多并发、长输入 + 高频流式反馈的场景下，计算核心争抢显存带宽导致的线程排队现象仍然存在 [35]。

## 竞品应对策略

从硅基流动的技术路线中可以提炼几点：

1. 推理性能的竞争重心在向软硬协同转移。Python 层调度优化的空间已经不大，需要深入到物理通信总线（UB-Mesh）和算子层面（MLAProlog、NZ 格式 KV Cache）。MoE 时代，谁能更好地利用底层硬件特性，谁就有吞吐优势。

2. 边缘卸载是一条有效的商业路径。BizyAir 这类 Serverless 插件让无 GPU 的终端也能用上大模型，实际效果是把分散的计算需求集中到私有云资源池，提高客户粘性。

3. 底层调优技术（INT8 量化、BSND 布局）能直接转化为商业溢价。硅基流动把这些能力锁在企业版 License 里说明一件事：只要调优能帮客户省下看得见的硬件成本，技术本身就是产品。

硅基流动的优势不在于接入了多少种开源模型，而在于 CloudMatrix-Infer 和 OneDiff Enterprise 这套底层推理引擎。竞品要追赶，需要在三个方向投入：异构集群的分布式缓存共享、跨硬件的算子融合编译框架、以及能适应不规则负载的微批次流水线调度。

#### Works cited

1. Serving Large Language Models on Huawei ... - arXiv.org, accessed February 26, 2026, https://arxiv.org/abs/2506.12708
2. [Literature Review] Serving Large Language Models on Huawei CloudMatrix384, accessed February 26, 2026, https://www.themoonlight.io/en/review/serving-large-language-models-on-huawei-cloudmatrix384
3. Serving Large Language Models on Huawei CloudMatrix384 - arXiv, accessed February 26, 2026, https://arxiv.org/html/2506.12708v1
4. Serving Large Language Models on Huawei CloudMatrix384 - arXiv.org, accessed February 26, 2026, https://arxiv.org/pdf/2506.12708
5. SiliconFlow: Product introduction, accessed February 26, 2026, https://docs.siliconflow.com/
6. Enterprise-Level MaaS Emerges! How Does Silicon Flow Help in the Industrialization of Large Models? - AI NEWS, accessed February 26, 2026, https://news.aibase.com/news/21458
7. Pull requests · siliconflow/onediff - GitHub, accessed February 26, 2026, https://github.com/siliconflow/onediff/pulls
8. OneDiff: An out-of-the-box acceleration library for diffusion models. - GitHub, accessed February 26, 2026, https://github.com/siliconflow/onediff
9. siliconflow repositories - GitHub, accessed February 26, 2026, https://github.com/orgs/siliconflow/repositories
10. Accelerating Stable Video Diffusion 3x faster with OneDiff DeepCache + Int8 | by SiliconFlow, accessed February 26, 2026, https://medium.com/@SiliconFlowAI/accelerating-stable-video-diffusion-3x-faster-with-onediff-deepcache-int8-92a37d20ed9a
11. Running Stable Video Diffusion 2x Faster with OneDiff DeepCache Node - Reddit, accessed February 26, 2026, https://www.reddit.com/r/StableDiffusion/comments/18mshfv/running_stable_video_diffusion_2x_faster_with/
12. onediff/README_ENTERPRISE.md at main - GitHub, accessed February 26, 2026, https://github.com/siliconflow/onediff/blob/main/README_ENTERPRISE.md
13. onediff - PyPI, accessed February 26, 2026, https://pypi.org/project/onediff/
14. siliconflow/onediff_releases - GitHub, accessed February 26, 2026, https://github.com/siliconflow/onediff_releases
15. Home · siliconflow/onediff Wiki - GitHub, accessed February 26, 2026, https://github.com/siliconflow/onediff/wiki
16. SiliconFlow - GitHub, accessed February 26, 2026, https://github.com/siliconflow
17. BizyAir Nodes, accessed February 26, 2026, https://siliconflow.github.io/BizyAir/index.html
18. README.md - siliconflow/ChatGPT-Next-Web · GitHub, accessed February 26, 2026, https://github.com/siliconflow/ChatGPT-Next-Web/blob/main/README.md
19. Why is vLLM Outperforming TensorRT-LLM (Nvidia's deployment library)? My Shocking Benchmarks on GPT-OSS-120B with H100 : r/LocalLLaMA - Reddit, accessed February 26, 2026, https://www.reddit.com/r/LocalLLaMA/comments/1oyawkl/why_is_vllm_outperforming_tensorrtllm_nvidias/
20. Fireworks AI: Optimized Inference Solutions, accessed February 26, 2026, https://createaiagent.net/tools/fireworks-ai/
21. Ultimate Guide – The Best Model as a Service (MaaS) Platforms of 2026 - SiliconFlow, accessed February 26, 2026, https://www.siliconflow.com/articles/en/the-best-model-as-a-service-maas
22. 硅基流动企业级MaaS平台, accessed February 26, 2026, https://siliconflow.cn/enterprise
23. vLLM vs TensorRT-LLM: Key differences, performance, and how to run them - Northflank, accessed February 26, 2026, https://northflank.com/blog/vllm-vs-tensorrt-llm-and-how-to-run-them
24. CloudMatrix384 with Ascend 910/920: How DeepSeek Cuts AI Costs by 90% vs Nvidia H100, accessed February 26, 2026, https://gpuvec.com/posts/huawei_and_deepseek
25. Quickstart - SiliconFlow, accessed February 26, 2026, https://docs.siliconflow.cn/en/userguide/quickstart
26. Quick Start - SiliconFlow, accessed February 26, 2026, https://docs.siliconflow.com/en/userguide/quickstart
27. Product introduction - SiliconFlow, accessed February 26, 2026, https://docs.siliconflow.cn/en/userguide/introduction
28. 硅基流动入局企业级MaaS，重写大模型落地叙事 - 雷峰网, accessed February 26, 2026, https://m.leiphone.com/category/ai/Ms2WQ4Ufh4PZWX8H.html
29. Ultimate Guide – The Best Scalable Fine-Tuning Infrastructure of 2026 - SiliconFlow, accessed February 26, 2026, https://www.siliconflow.com/articles/en/the-most-scalable-fine-tuning-infrastructure
30. 硅基流动科技申请基于MLA的稀疏LLM的数据并行处理系统及方法专利 - 凤凰网, accessed February 26, 2026, https://i.ifeng.com/c/8ks1Qgr8mhG
31. 硅基流动申请基于大语言模型的交互式图像处理方法及装置专利 - 新浪财经, accessed February 26, 2026, https://cj.sina.cn/articles/view/1704103183/65928d0f02007mq8o?froms=ggmp
32. InstantID can run 1.8x Faster with OneDiff : r/StableDiffusion - Reddit, accessed February 26, 2026, https://www.reddit.com/r/StableDiffusion/comments/1al19ek/instantid_can_run_18x_faster_with_onediff/
33. not much happened today - AINews, accessed February 26, 2026, https://news.smol.ai/issues/25-11-03-not-much/
34. News Posts matching 'DeepSeek' - TechPowerUp, accessed February 26, 2026, https://www.techpowerup.com/news-tags/DeepSeek
35. xLLM Technical Report - arXiv.org, accessed February 26, 2026, https://arxiv.org/html/2510.14686v1
