PYTHON ?= python3
BEACON_ROOT ?= .cache/beacon
BEACON_PROFILE := $(BEACON_ROOT)/templates/research-paper
BUILD_ROOT ?= build
THEME ?= egohygiene

.PHONY: all beacon build check check-all inventory

all: check

beacon:
	$(PYTHON) "scripts/resolve_beacon.py" --destination "$(BEACON_ROOT)"

build: beacon
	$(PYTHON) "$(BEACON_PROFILE)/scripts/build.py" \
		--project "$(CURDIR)" \
		--output "$(CURDIR)/$(BUILD_ROOT)/$(THEME)" \
		--theme "$(THEME)"

check: build inventory
	$(PYTHON) "$(BEACON_PROFILE)/scripts/check.py" \
		--project "$(CURDIR)" \
		--build-dir "$(CURDIR)/$(BUILD_ROOT)/$(THEME)" \
		--theme "$(THEME)" \
		--compile-arxiv

check-all:
	$(MAKE) check THEME="neutral"
	$(MAKE) check THEME="egohygiene"

inventory:
	$(PYTHON) "scripts/check_source_inventory.py"
