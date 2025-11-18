# llm-d CPU Simulated Accelerator Guide <span style="float:right;">[中文](llm-d-cpu-sim-guide_zh.md)</span>

> Goal: Reproduce the full llm-d serving pipeline (Gateway + EPP + routing sidecar) on a macOS host without GPUs by using kind + Istio together with the CPU-based simulator defined in `guides/simulated-accelerators`.

## Background

The `simulated-accelerators` guide is an officially supported “supporting path.” It relies on the `ghcr.io/llm-d/llm-d-inference-sim` image to emulate vLLM pods on CPU-only nodes, while keeping the real Gateway API Inference Extension components in place. This allows you to get comfortable with Helmfile layouts, routing policies, and monitoring integrations without provisioning GPUs or downloading HuggingFace models.

## Prerequisites

Run the official dependency installer to obtain gh, kind, kubectl, helm, helmfile, yq, git, and the `helm-diff` plugin in one shot:

```bash
bash guides/prereq/client-setup/install-deps.sh --dev
```

If you prefer managing tooling manually, make sure every binary is on `PATH` and install the Helm plugin explicitly:

```bash
helm plugin install https://github.com/databus23/helm-diff
```

## Image Preparation

The default charts pull images from gcr.io, registry.k8s.io, and ghcr.io. In regions where these registries are blocked, mirror them to:

- `gcr.io` → `gcr.m.daocloud.io`
- `registry.k8s.io` → `k8s.m.daocloud.io`
- `ghcr.io` → `ghcr.m.daocloud.io`

If the kind nodes cannot reach the registry directly, preload the images on the host and inject them into the cluster:

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

## Fetch the Source

Clone the repository and treat its root directory as the working tree for all subsequent commands:

```bash
gh repo clone llm-d/llm-d  # or git clone https://github.com/llm-d/llm-d.git
cd llm-d
```

## Prepare the kind Cluster

Create a minimal kind topology. The following config exposes NodePort 30080/30443 to the host (8000/8443). Remove `extraPortMappings` if you plan to rely solely on port-forward (this guide continues to use port-forward):

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

## Install Gateway API & Inference Extension CRDs

Ensure `kubectl config current-context` points to the kind cluster, then run:

```bash
bash guides/prereq/gateway-provider/install-gateway-provider-dependencies.sh
```

This installs Gateway API v1.3.0 and Gateway API Inference Extension v1.0.1 CRDs.

## Deploy the Istio Control Plane

Use the provided Helmfile (already pointing to Daocloud mirrors) to deploy `istio-base` + `istiod`:

```bash
helmfile apply -f guides/prereq/gateway-provider/istio.helmfile.yaml
```

Verify readiness via `kubectl get pods -n istio-system`.

## Deploy the llm-d-sim Stack

`guides/simulated-accelerators` installs three charts:

1. `infra-sim`: Gateway resources.
2. `gaie-sim`: InferencePool + Endpoint Picker.
3. `ms-sim`: Prefill/Decode simulator pods.

By default, PodMonitor/ServiceMonitor objects are created. If Prometheus/Grafana are not yet installed, disable them:

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

Prefill and Decode both use `ghcr.m.daocloud.io/llm-d/llm-d-inference-sim:v0.6.1`, so no HuggingFace token is required.

Deployment:

```bash
export NAMESPACE=llm-d-sim
kubectl create namespace ${NAMESPACE}

cd guides/simulated-accelerators
helmfile apply -n ${NAMESPACE}
kubectl apply -f httproute.yaml -n ${NAMESPACE}
cd ../..
```

## Validate the Deployment

Once all pods are Ready, inspect releases, workloads, and HTTPRoute status:

```bash
helm list -n llm-d-sim
kubectl get pods -n llm-d-sim
kubectl get httproute -n llm-d-sim
kubectl get httproute llm-d-sim -n llm-d-sim -o yaml | yq '.status.parents'
```

Proceed to testing only after the HTTPRoute reports both `Accepted=True` and `Programmed=True`.

## Functional Test

Expose the Gateway via port-forward (keep the command running):

```bash
kubectl port-forward -n ${NAMESPACE} service/infra-sim-inference-gateway-istio 8000:80
```

In another terminal, issue OpenAI-compatible requests:

```bash
export ENDPOINT=http://localhost:8000
curl -s ${ENDPOINT}/v1/models | jq
curl -s ${ENDPOINT}/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"random","prompt":"Hello, simulator!","max_tokens":32}' | jq
```

> If you kept the NodePort/hostPort mapping, you can hit `http://localhost:8000` directly without port-forward. Choose whichever method suits your workflow.

## Cleanup

When finished, tear everything down:

```bash
cd guides/simulated-accelerators
helmfile destroy -n ${NAMESPACE}
kubectl delete -f httproute.yaml -n ${NAMESPACE}
cd ../..

helmfile destroy -f guides/prereq/gateway-provider/istio.helmfile.yaml
kind delete cluster --name llmd-sim
```

You now have a repeatable CPU-only path for validating llm-d components. When ready to move to real models (e.g., `guides/inference-scheduling`), reuse the same workflow but swap in the appropriate model artifacts and runtime images.
