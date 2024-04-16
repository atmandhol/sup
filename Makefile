BINARY = sup
build:
	@go build -o $(BINARY)

run:
	go run .

start: build
	./$(BINARY)

test: prepare
	go test ./...

all: lint build

.PHONY: gomod
gomod: ## Update go module dependencies
	go mod tidy -v

.PHONY: prepare
prepare: gomod vet


.PHONY: require-%
require-%: ## Checks if the required command exists on the command line
	@if ! command -v $* 1> /dev/null 2>&1; then echo "$* CLI not installed or found in PATH"; exit 1; fi

.PHONY: vet
vet: ## Run go vet against code
	go vet ./...
