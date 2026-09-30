BOLD  := \033[1m
CYAN  := \033[36m
GREEN := \033[32m
RESET := \033[0m

.DEFAULT_GOAL := help

# ── Maintenance ──────────────────────────────────────────────────────────────

.PHONY: clean

clean: ## Remove build artifacts
	rm -rf bin

# ── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "; printf "\n$(BOLD)samzong$(RESET) — GitHub profile and personal notes\n"} \
		/^# ── / {n = $$0; gsub(/(^# ── | (─)+$$)/, "", n); printf "\n$(BOLD)%s$(RESET)\n", n} \
		/^[a-zA-Z0-9_-]+:.*## / {printf "  $(CYAN)make %-10s$(RESET) %s\n", $$1, $$2} \
		END {printf "\n"}' $(MAKEFILE_LIST)
