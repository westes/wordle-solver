.PHONY: check

check:
	.venv/bin/pytest tests/ -v
