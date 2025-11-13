# llm-d CPU Simulated Accelerator Guide <span style="float:right;">[English](llm-d-cpu-sim-guide.md)</span>

> 目标：在一台 macOS 主机上，通过 kind + Istio 在 CPU 环境复刻 llm-d 的调度链路，使用 `guides/simulated-accelerators` 中的无模型模拟器体验调度、路由、监控等关键组件。

## 背景

`simulated-accelerators` 是 llm-d 官方指南中的 supporting guide，使用 `ghcr.io/llm-d/llm-d-inference-sim` 镜像在 CPU 上模拟 vLLM 的行为，配合真实的 Gateway/Inference Scheduler，可以让你在没有 GPU 的情况下熟悉 llm-d 的部署拓扑、Helm chart 结构以及 Gateway API Inference Extension 的工作流。模拟器不会从 HuggingFace 下载模型，因此适合在笔记本或 CI 环境进行功能验证、调度策略实验以及监控集成演练。

## 前置工具

最便捷的方式是运行官方依赖脚本，一次性安装 gh、kind、kubectl、helm、helmfile、yq、git 等客户端工具以及 `helm-diff` 插件：

```bash
bash guides/prereq/client-setup/install-deps.sh --dev
```

如需手动安装，请确保各二进制已添加到 `PATH`，并执行：

```bash
helm plugin install https://github.com/databus23/helm-diff
```

## 镜像准备

默认镜像分别托管在 gcr.io、registry.k8s.io、ghcr.io，如在国内网络环境可替换为：

- `gcr.io` → `gcr.m.daocloud.io`
- `registry.k8s.io` → `k8s.m.daocloud.io`
- `ghcr.io` → `ghcr.m.daocloud.io`

模拟器依赖的镜像可以先在宿主机拉取，再通过 `kind load docker-image` 注入（确保 kind 集群已创建）：

```bash
#!/usr/bin/env bash
set -euo pipefail

KIND_CLUSTER_NAME=${KIND_CLUSTER_NAME:-llmd-sim}
IMAGES=(
  "gcr.m.daocloud.io/istio-testing/pilot:1.28-alpha.89f30b26ba71bf5e538083a4720d0bc2d8c06401"
  "gcr.m.daocloud.io/istio-testing/proxyv2:1.28-alpha.89f30b26ba71bf5e538083a4720d0bc2d8c06401"
  "ghcr.m.daocloud.io/llm-d/llm-d-inference-scheduler:v0.3.2"
  "ghcr.m.daocloud.io/llm-d/llm-d-routing-sidecar:v0.3.0"
  "ghcr.m.daocloud.io/llm-d/llm-d-inference-sim:v0.6.1"
)

for img in "${IMAGES[@]}"; do
  docker image inspect "$img" >/dev/null 2>&1 || docker pull "$img"
  kind load docker-image "$img" --name "$KIND_CLUSTER_NAME"
done
```

## 获取代码

使用 gh CLI 或 git 同步仓库，所有相对路径均以仓库根目录为基准：

```bash
gh repo clone llm-d/llm-d  # 或 git clone https://github.com/llm-d/llm-d.git
cd llm-d
```

## 准备 kind 集群

创建最小可运行的 kind 环境。下列配置会把 NodePort 30080/30443 暴露到宿主 8000/8443；如果你更倾向于仅使用 port-forward，可移除 `extraPortMappings`（本文示例仍采用 port-forward）：

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: llmd-sim
networking:
  disableDefaultCNI: false
  kubeProxyMode: iptables
nodes:
  - role: control-plane
    image: kindest/node:v1.31.0
    extraPortMappings:
      - containerPort: 30080
        hostPort: 8000
        protocol: TCP
      - containerPort: 30443
        hostPort: 8443
        protocol: TCP
  - role: worker
    image: kindest/node:v1.31.0
```

```bash
kind create cluster --config kind-config.yaml
```

## 安装 Gateway API 与 Inference Extension CRD

确保当前 kubeconfig 已指向 kind 集群，然后执行：

```bash
bash guides/prereq/gateway-provider/install-gateway-provider-dependencies.sh
```

该脚本会安装 Gateway API v1.3.0 与 Gateway API Inference Extension v1.0.1 的 CRD，请勿跳过。

## 部署 Istio 控制面

使用仓库提供的 Helmfile 拉起 Istio base + istiod（已指向 Daocloud 镜像）：

```bash
helmfile apply -f guides/prereq/gateway-provider/istio.helmfile.yaml
```

完成后可以用 `kubectl get pods -n istio-system` 验证 istiod 是否 Ready。

## 部署 llm-d-sim

`guides/simulated-accelerators` 会一次性安装三组 chart：

1. `infra-sim`：Gateway + GatewayClass 等基础设施
2. `gaie-sim`：InferencePool（EPP/调度器）
3. `ms-sim`：Prefill/Decode 模拟器

默认会创建 PodMonitor/ServiceMonitor。若还未部署监控组件，可先关闭：

- 编辑 `guides/simulated-accelerators/ms-sim/values.yaml` 关闭 Prefill/Decode PodMonitor
- 编辑 `guides/simulated-accelerators/gaie-sim/values.yaml` 关闭 EPP 的 Prometheus Monitor

```yaml
# guides/simulated-accelerators/ms-sim/values.yaml
decode:
  monitoring:
    podmonitor:
      enabled: false
prefill:
  monitoring:
    podmonitor:
      enabled: false

# guides/simulated-accelerators/gaie-sim/values.yaml
inferenceExtension:
  monitoring:
    prometheus:
      enabled: false
```

在模拟器场景下，Prefill/Decode 复用 `ghcr.m.daocloud.io/llm-d/llm-d-inference-sim:v0.6.1`，不需要 HuggingFace Token Secret。

正式部署：

```bash
export NAMESPACE=llm-d-sim
kubectl create namespace ${NAMESPACE}

cd guides/simulated-accelerators
helmfile apply -n ${NAMESPACE}
kubectl apply -f httproute.yaml -n ${NAMESPACE}
cd ../..
```

## 验证部署

等待所有 Pod Ready 后，检查 Helm release、工作负载与 HTTPRoute：

```bash
helm list -n llm-d-sim
kubectl get pods -n llm-d-sim
kubectl get httproute -n llm-d-sim
kubectl get httproute llm-d-sim -n llm-d-sim -o yaml | yq '.status.parents'
```

当 HTTPRoute 的 `Accepted` 与 `Programmed` 条件均为 `True` 时，即可开始流量测试。

## 功能测试

使用 port-forward 暴露 Gateway Service，并在新终端发起 OpenAI 兼容请求：

```bash
kubectl port-forward -n ${NAMESPACE} service/infra-sim-inference-gateway-istio 8000:80  # 保持运行
```

```bash
# 另开终端
export ENDPOINT=http://localhost:8000
curl -s ${ENDPOINT}/v1/models | jq
curl -s ${ENDPOINT}/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"random","prompt":"kind 模拟器你好","max_tokens":32}' | jq
```

## 清理环境

体验完成后，可按顺序清理资源：

```bash
cd guides/simulated-accelerators
helmfile destroy -n ${NAMESPACE}
kubectl delete -f httproute.yaml -n ${NAMESPACE}
cd ../..

helmfile destroy -f guides/prereq/gateway-provider/istio.helmfile.yaml
kind delete cluster --name llmd-sim
```

至此，基于 CPU 模拟器的 llm-d 体验流程结束，下一步可以切换到 `guides/inference-scheduling` 等真实模型部署路径。
