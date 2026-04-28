.DEFAULT_GOAL := help
.PHONY: help clean

help: ## Show available targets
	@echo "Usage: make <target>"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

clean: ## Remove build artifacts
	rm -rf bin
