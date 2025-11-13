#!/usr/bin/env bash
set -euo pipefail

# Scripted version of guides/simulated-accelerators/llm-d-cpu-sim-guide.md
# Performs end-to-end CPU simulator deployment on kind + Istio.
# Usage: ./scripts/setup-llmd-sim.sh [--skip-kind] [--skip-images] [--skip-monitor-disable]

WORKDIR=$(git rev-parse --show-toplevel)
cd "$WORKDIR"

NAMESPACE=${NAMESPACE:-llm-d-sim}
KIND_CLUSTER_NAME=${KIND_CLUSTER_NAME:-llmd-sim}
KIND_CONFIG=${KIND_CONFIG:-kind-config.yaml}
SIM_DIR="guides/simulated-accelerators"

declare -a IMAGES=(
  "gcr.m.daocloud.io/istio-testing/pilot:1.28-alpha.89f30b26ba71bf5e538083a4720d0bc2d8c06401"
  "gcr.m.daocloud.io/istio-testing/proxyv2:1.28-alpha.89f30b26ba71bf5e538083a4720d0bc2d8c06401"
  "ghcr.m.daocloud.io/llm-d/llm-d-inference-scheduler:v0.3.2"
  "ghcr.m.daocloud.io/llm-d/llm-d-routing-sidecar:v0.3.0"
  "ghcr.m.daocloud.io/llm-d/llm-d-inference-sim:v0.6.1"
)

RUN=false
SKIP_KIND=false
SKIP_IMAGES=false
SKIP_MONITOR_PATCH=false

usage() {
  cat <<'USAGE'
Usage: scripts/setup-llmd-sim.sh --run [options]

Options:
  --run                        Execute the full simulator deployment flow.
  --skip-kind                  Skip kind cluster creation (assumes existing cluster).
  --skip-images                Skip docker pull + kind load steps.
  --skip-monitor-disable       Keep default PodMonitor/ServiceMonitor settings.
  -h, --help                   Show this help message and exit.

If --run is not supplied, the script prints this help text.
USAGE
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --run) RUN=true ; shift ;;
    --skip-kind) SKIP_KIND=true ; shift ;;
    --skip-images) SKIP_IMAGES=true ; shift ;;
    --skip-monitor-disable) SKIP_MONITOR_PATCH=true ; shift ;;
    -h|--help) usage ; exit 0 ;;
    *) echo "Unknown flag $1" >&2 ; usage ; exit 1 ;;
  esac
done

if ! $RUN; then
  usage
  exit 0
fi

create_kind_cluster() {
  if $SKIP_KIND; then
    echo "[kind] skipping cluster creation"
    return
  fi
  cat > "$KIND_CONFIG" <<'YAML'
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
YAML
  kind create cluster --name "$KIND_CLUSTER_NAME" --config "$KIND_CONFIG"
}

load_images() {
  if $SKIP_IMAGES; then
    echo "[images] skipping preload"
    return
  fi
  for img in "${IMAGES[@]}"; do
    docker image inspect "$img" >/dev/null 2>&1 || docker pull "$img"
    kind load docker-image "$img" --name "$KIND_CLUSTER_NAME"
  done
}

install_crds() {
  bash guides/prereq/gateway-provider/install-gateway-provider-dependencies.sh
}

deploy_istio() {
  helmfile apply -f guides/prereq/gateway-provider/istio.helmfile.yaml
}

patch_monitoring_flags() {
  if $SKIP_MONITOR_PATCH; then
    echo "[monitor] keeping defaults"
    return
  fi
  yq -i '(.decode.monitoring.podmonitor.enabled = false) | (.prefill.monitoring.podmonitor.enabled = false)' "$SIM_DIR/ms-sim/values.yaml"
  yq -i '.inferenceExtension.monitoring.prometheus.enabled = false' "$SIM_DIR/gaie-sim/values.yaml"
}

install_sim_stack() {
  kubectl get ns "$NAMESPACE" >/dev/null 2>&1 || kubectl create namespace "$NAMESPACE"
  (cd "$SIM_DIR" && helmfile apply -n "$NAMESPACE")
  kubectl apply -f "$SIM_DIR/httproute.yaml" -n "$NAMESPACE"
}

verify_stack() {
  echo "[verify] helm releases"
  helm list -n "$NAMESPACE"
  echo "[verify] pods"
  kubectl get pods -n "$NAMESPACE"
  echo "[verify] httproute"
  kubectl get httproute -n "$NAMESPACE"
  kubectl get httproute llm-d-sim -n "$NAMESPACE" -o yaml | yq '.status.parents'
}

main() {
  create_kind_cluster
  load_images
  install_crds
  deploy_istio
  patch_monitoring_flags
  install_sim_stack
  verify_stack
  cat <<'NOTE'

Deployment complete. To test:
  kubectl port-forward -n ${NAMESPACE} service/infra-sim-inference-gateway-istio 8000:80
  curl -s http://localhost:8000/v1/models | jq
NOTE
}

main
