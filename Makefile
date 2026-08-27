PYTHON ?= python3
PROJECT ?= auto
THEME ?= egohygiene
BUILD_DIR ?= build/$(THEME)
TASK := $(PYTHON) scripts/tasks.py --project="$(PROJECT)" --build-dir="$(BUILD_DIR)" --theme="$(THEME)" --python="$(PYTHON)"

.PHONY: all beacon-build beacon-doctor beacon-package beacon-plan beacon-validate bootstrap-check build check check-all check-content check-links check-site clean inventory mvp-bootstrap mvp-check mvp-contracts mvp-contracts-check mvp-format mvp-lint mvp-test reproducibility site test

all: build

build:
	$(TASK) build

check:
	$(TASK) check

check-all:
	$(TASK) check-all

check-content:
	$(TASK) check-content

check-links:
	$(TASK) check-links

reproducibility:
	$(TASK) reproducibility

bootstrap-check:
	$(TASK) bootstrap-check

clean:
	$(TASK) clean

inventory:
	$(TASK) inventory

mvp-bootstrap:
	$(TASK) mvp-bootstrap

mvp-check:
	$(TASK) mvp-check

mvp-contracts:
	$(TASK) mvp-contracts

mvp-contracts-check:
	$(TASK) mvp-contracts-check

mvp-format:
	$(TASK) mvp-format

mvp-lint:
	$(TASK) mvp-lint

mvp-test:
	$(TASK) mvp-test

site:
	$(TASK) site

check-site:
	$(TASK) check-site

test:
	$(TASK) test

beacon-validate:
	$(PYTHON) scripts/beacon.py validate

beacon-doctor:
	$(PYTHON) scripts/beacon.py doctor

beacon-plan:
	$(PYTHON) scripts/beacon.py plan

beacon-build:
	$(PYTHON) scripts/beacon.py build

beacon-package:
	$(PYTHON) scripts/beacon.py package
