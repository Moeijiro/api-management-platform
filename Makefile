# Developer shortcuts. The README lists the raw commands too.

BACKEND := backend
VENV := $(BACKEND)/.venv/bin

.PHONY: help install api web test traffic purge-logs clean

help:
	@echo "make install    install backend + frontend dependencies"
	@echo "make api        run the FastAPI backend on :8000"
	@echo "make web        run the dashboard on :5173"
	@echo "make test       run the backend test suite"
	@echo "make traffic    send real requests to a running API (demo data)"
	@echo "make purge-logs delete request logs past the retention window"

install:
	python3 -m venv $(BACKEND)/.venv
	$(VENV)/pip install -r $(BACKEND)/requirements-dev.txt
	cd frontend && npm install

api:
	cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

test:
	cd $(BACKEND) && .venv/bin/python -m pytest

traffic:
	cd $(BACKEND) && .venv/bin/python scripts/generate_traffic.py --requests 150

purge-logs:
	cd $(BACKEND) && .venv/bin/python -m app.cli purge-logs

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -f $(BACKEND)/*.db $(BACKEND)/*.db-wal $(BACKEND)/*.db-shm
