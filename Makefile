PYTHON ?= python3
PORT ?= 8787
export HL_DATASET_URI ?= $(CURDIR)/demo/data
export HL_LLM_PROVIDER ?= mock

.PHONY: install test run record demo

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	HL_DATASET_URI=$(CURDIR)/demo/data HL_LLM_PROVIDER=mock $(PYTHON) -m pytest

run:
	HL_DATASET_URI=$(CURDIR)/demo/data HL_LLM_PROVIDER=$${HL_LLM_PROVIDER:-mock} \
		$(PYTHON) -m uvicorn agent_gate.api:create_app --factory --host 127.0.0.1 --port $(PORT)

record:
	HL_DATASET_URI=$(CURDIR)/demo/data HL_LLM_PROVIDER=mock $(PYTHON) -m agent_gate.record

demo: record
	$(PYTHON) -m http.server 8088 --directory site
