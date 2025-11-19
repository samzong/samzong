# How to add a new command (example: foo)
# 1) Add the command name to CMDS:      CMDS := mirrormate opentalk foo
# 2) Map its source file:               SRC_foo := path/to/foo.go
# 3) Add a build alias target:          build-foo: $(BIN_DIR)/foo ## Build foo
#                                       	@true
# 4) (Optional) Add to .PHONY:          .PHONY: help build-all build-mirrormate build-opentalk build-foo clean
# Note: build-all automatically builds all names listed in CMDS.

BIN_DIR := bin
CMDS := mirrormate opentalk
GOFLAGS := -trimpath -ldflags "-s -w"

SRC_mirrormate := tools/mirrormate.go
SRC_opentalk := talks/opentalk.go

.DEFAULT_GOAL := help

.PHONY: help build-all build-mirrormate build-opentalk clean

help: ## Show available targets
	@echo "Usage: make <target>"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

define build_cmd_rule
$(BIN_DIR)/$(1): $$(SRC_$(1))
	mkdir -p $(BIN_DIR)
	CGO_ENABLED=0 go build $(GOFLAGS) -o $$@ $$<
endef

$(foreach c,$(CMDS),$(eval $(call build_cmd_rule,$(c))))

build-all: $(addprefix $(BIN_DIR)/,$(CMDS)) ## Build all commands
	@for c in $(CMDS); do \
		if [ -x "$(BIN_DIR)/$$c" ]; then \
			echo "Built $$c: $(BIN_DIR)/$$c"; \
		else \
			echo "Build failed: $(BIN_DIR)/$$c"; exit 1; \
		fi; \
	done

build-mirrormate: $(BIN_DIR)/mirrormate ## Build mirrormate
	@[ -x $(BIN_DIR)/mirrormate ] && echo "Built mirrormate: $(BIN_DIR)/mirrormate" || { echo "Build failed: $(BIN_DIR)/mirrormate"; exit 1; }

build-opentalk: $(BIN_DIR)/opentalk ## Build opentalk
	@[ -x $(BIN_DIR)/opentalk ] && echo "Built opentalk: $(BIN_DIR)/opentalk" || { echo "Build failed: $(BIN_DIR)/opentalk"; exit 1; }

clean: ## Remove bin directory
	rm -rf $(BIN_DIR)
