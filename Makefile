.PHONY: test install

install:
	uv sync

test:            ## Run template tests
	uv run pytest tests/ -v
