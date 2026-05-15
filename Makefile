.PHONY: install lint typecheck test dev migrate proto

# ── Backend ───────────────────────────────────────────────────────────────────
install:
	pip install -r backend/requirements/dev.txt
	cd frontend && npm ci

lint:
	cd backend && ruff check . && black --check .
	cd frontend && npm run lint && npm run format:check

typecheck:
	cd backend && mypy app
	cd frontend && npm run typecheck

test:
	cd backend && pytest --cov=app --cov-report=term-missing
	cd frontend && npm test -- --passWithNoTests

# ── Dev servers ───────────────────────────────────────────────────────────────
dev:
	docker compose up -d db
	cd backend && uvicorn app.main:app --reload --port 8000 &
	cd frontend && npm run dev

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	cd backend && alembic upgrade head

# ── gRPC ──────────────────────────────────────────────────────────────────────
proto:
	cd backend && python -m grpc_tools.protoc \
		-I proto \
		--python_out=app/grpc/generated \
		--grpc_python_out=app/grpc/generated \
		proto/library.proto
