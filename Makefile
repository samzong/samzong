BIN_DIR := bin
SRC := tools/mirrormate.go
OS := $(shell uname -s)

.PHONY: build build-macos build-linux clean

build:
ifeq ($(OS),Darwin)
	mkdir -p $(BIN_DIR)
	CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o $(BIN_DIR)/mirrormate $(SRC)
else
	mkdir -p $(BIN_DIR)
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -tags netgo -trimpath -ldflags "-s -w" -o $(BIN_DIR)/mirrormate-linux-amd64 $(SRC)
endif

build-macos:
	mkdir -p $(BIN_DIR)
	CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o $(BIN_DIR)/mirrormate $(SRC)

build-linux:
	mkdir -p $(BIN_DIR)
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -tags netgo -trimpath -ldflags "-s -w" -o $(BIN_DIR)/mirrormate-linux-amd64 $(SRC)

clean:
	rm -rf $(BIN_DIR)