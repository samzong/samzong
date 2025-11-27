# 大纲

本次分享面向刚想摸索大模型的人：我会从“想玩大模型？怎么在电脑上跑？”开始，逐步讲清文本/图像生成的基本路径、服务器端可用工具，以及分布式/分体式推理的主要框架；定位“零门槛、最简单”的方式，带你从单机过渡到集群，再介绍几款能在本地或离线环境实用的小工具，并预告我们接下来在大模型方向的主要产品路线。

- 先回顾几个单体部署方案，重点呈现快速上线与本地资源利用之间的权衡
- 介绍代表性的分布式部署模式，分析其在调度、扩缩、流量隔离上的实践
- 最后梳理部署所需的关键依赖，并由此延伸相关能力
  - Gateway 分层架构（控制面/数据面分离的价值）
  - KVCache（洞察缓存策略的作用）
  - nixl-connector 的角色（面对不同模型的接入方案）
  - 最简化的模型下载流程
  - 顺带提及我的开源项目




Candidates (name → GitHub):
- vLLM → https://github.com/vllm-project/vllm
- Text Generation Inference (TGI) → https://github.com/huggingface/text-generation-inference
- SGLang → https://github.com/sglang-ai/sglang
- LMDeploy → https://github.com/InternLM/lmdeploy
- FastChat → https://github.com/lm-sys/FastChat
- LightLLM → https://github.com/ModelTC/LightLLM
- TensorRT-LLM → https://github.com/NVIDIA/TensorRT-LLM
- Triton Inference Server → https://github.com/triton-inference-server/server
- DeepSpeed (Inference) → https://github.com/microsoft/DeepSpeed
- DeepSpeed-MII → https://github.com/microsoft/DeepSpeed-MII
- ColossalAI → https://github.com/hpcaitech/ColossalAI
- KServe → https://github.com/kserve/kserve
- Ray Serve → https://github.com/ray-project/ray
- llama.cpp → https://github.com/ggerganov/llama.cpp
- Ollama → https://github.com/ollama/ollama
- MLC LLM → https://github.com/mlc-ai/mlc-llm
- ExLlamaV2 → https://github.com/turboderp/exllamav2
- GGML → https://github.com/ggerganov/ggml
- ONNX Runtime GenAI → https://github.com/microsoft/onnxruntime-genai
- OpenVINO → https://github.com/openvinotoolkit/openvino
- Candle → https://github.com/huggingface/candle
- Xinference → https://github.com/xorbitsai/inference
- Text Generation Web UI → https://github.com/oobabooga/text-generation-webui
- KoboldCPP → https://github.com/LostRuins/koboldcpp
- BentoML → https://github.com/bentoml/BentoML
- OpenLLM → https://github.com/bentoml/OpenLLM
- Petals → https://github.com/bigscience-workshop/petals
- llm-d → https://github.com/llm-d/llm-d
- NVIDIA Dynamo → https://github.com/ai-dynamo/dynamo
- Grove (K8s API for inference) → https://github.com/ai-dynamo/grove
- vLLM Production Stack → https://github.com/vllm-project/production-stack
- AIBrix → https://github.com/vllm-project/aibrix
- SGLang OME (Operator) → https://github.com/sgl-project/ome
- SGLang RBG (RoleBasedGroup) → https://github.com/sgl-project/rbg
- vLLM Router → https://github.com/LLM-inference-router/vllm-router
- LMCache → https://github.com/LMCache/LMCache
- InfiniStore → https://github.com/bytedance/InfiniStore
- NIXL (Inference Xfer Library) → https://github.com/ai-dynamo/nixl
- ModelMesh → https://github.com/kserve/modelmesh
- ModelMesh Serving → https://github.com/kserve/modelmesh-serving
- LeaderWorkerSet (K8s SIG) → https://github.com/kubernetes-sigs/lws
- JobSet (K8s SIG) → https://github.com/kubernetes-sigs/jobset
- Kthena (Volcano) → https://github.com/volcano-sh/kthena
