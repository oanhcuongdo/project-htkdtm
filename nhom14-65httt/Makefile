.PHONY: help dev dev-db stop migrate migrate-new migrate-check migrate-status seed load-vifoodrec test etl \
        lint-backend lint-frontend install-backend install-frontend

help: ## Hiển thị trợ giúp
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Docker ---
dev: ## Khởi động toàn bộ (DB + backend + frontend)
	docker compose up --build

dev-db: ## Chỉ khởi động PostgreSQL
	docker compose up db -d

stop: ## Dừng tất cả container
	docker compose down

# --- Backend (migration/seed dùng container; cài đặt/test dùng môi trường local) ---
install-backend: ## Cài gói Python
	cd src/backend && pip install -r requirements.txt -r requirements-dev.txt

migrate: ## Chạy migration lên bản mới nhất
	docker compose exec backend alembic upgrade head

migrate-new: ## Tạo migration mới (msg="mô tả")
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

migrate-check: ## Kiểm tra schema hiện tại so với models
	docker compose exec backend alembic check

migrate-status: ## Xem revision hiện tại của cơ sở dữ liệu
	docker compose exec backend alembic current

seed: ## Nạp dữ liệu mẫu
	docker compose exec backend python -m scripts.seed

load-vifoodrec: ## Nhập dữ liệu ViFoodRec
	docker compose exec backend python -m scripts.load_vifoodrec $(input)

test: ## Chạy toàn bộ test backend
	cd src/backend && python -m pytest tests/ -v

etl: ## Chạy ETL
	docker compose exec backend python -m app.etl.run_etl

lint-backend: ## Kiểm tra lint backend
	cd src/backend && ruff check . && ruff format --check .

# --- Frontend (chạy ngoài Docker) ---
install-frontend: ## Cài gói npm
	cd src/frontend && npm install

lint-frontend: ## Kiểm tra lint frontend
	cd src/frontend && npm run lint

build-frontend: ## Build frontend production
	cd src/frontend && npm run build
