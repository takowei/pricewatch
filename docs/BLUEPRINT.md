# PriceWatch — Production-Grade Backend 規格藍圖

> 旗艦公開作品集專案。目標：命中業界 hiring manager 對新鮮人/實習的硬標準——能 ship production、有 DB、有 auth、有測試、有 CI、可部署上線、有 live demo。
> 本檔 = Plan agent 藍圖 + 主對話（reviewer）硬標準審視修正。實作 builder 照此執行。

## 結論先行（TL;DR）

- **重用來源**：`~/workspace/sale-tracker/` 的 UNIQLO（官方 API，穩）/ NET 爬蟲解析 100% 可搬；`tracking.py` 的降價/達標偵測是「智識核心」，搬進 service 層、改成多使用者。**只讀 sale-tracker、不要改它**（另一個 agent 正在給它補測試）。
- **技術選型**：SQLModel + Alembic、APScheduler（非 Celery）、FastAPI 三層（router→service→repository）、JWT(access+refresh) + argon2、同步（psycopg3 sync）。
- **自刻 vs vibe-code**：自刻＝① auth/JWT ② 降價偵測演算法 ③ repository 層邊界 ④ DB schema。其餘（CRUD、Dockerfile、CI yaml、scraper 搬移）vibe-code。
- **可逆 vs 需 Root**：寫程式/本機跑/測試/CI 全可逆、自主做。需 Root（不可逆）＝開雲端機、買網域、設 DNS、放 production secrets、Telegram bot token。沙箱 docker 被封，compose 由 Root 在本機或既有 AWS Tokyo box 跑。

---

## 1. Repo 結構

```
pricewatch/
├── app/
│   ├── main.py                  # FastAPI app factory, router 掛載, lifespan(啟動 scheduler)
│   ├── core/
│   │   ├── config.py            # pydantic-settings 讀 env（DATABASE_URL, JWT_SECRET...）
│   │   ├── security.py          # ★自刻 密碼 hash、JWT 簽發/驗證
│   │   ├── logging.py           # ★審視補：結構化 logging 設定
│   │   ├── rate_limit.py        # ★審視補：auth 端點限速（slowapi 或自製）
│   │   └── deps.py              # FastAPI Depends: get_db, get_current_user
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   ├── models/                  # ★自刻 SQLModel ORM 表
│   │   ├── user.py product.py price_history.py watchlist.py alert.py
│   ├── schemas/                 # API DTO（SQLModel 不共用時）
│   ├── repositories/            # ★自刻邊界 純 DB 存取，無商業邏輯
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── watchlist_service.py
│   │   ├── alert_service.py     # ★自刻 降價/達標偵測（搬 tracking.py，寫成純函式）
│   │   └── ingest_service.py    # 爬蟲結果 → upsert product + price_history
│   ├── routers/                 # auth users products watchlist alerts health
│   ├── scrapers/                # 搬現有：uniqlo.py / net.py + base.py(Protocol)
│   └── jobs/
│       ├── scheduler.py         # APScheduler
│       └── tasks.py             # scrape_all → ingest → detect alerts → notify
├── frontend/                    # ★審視補：薄前端（沿用 sale-tracker React UI 接真 API）
├── alembic/ (env.py, versions/)
├── tests/
│   ├── conftest.py             # ★DB fixture（每 test 包 transaction rollback）
│   ├── test_auth.py test_watchlist_api.py test_alert_service.py
│   ├── test_integration_pipeline.py  # ★審視補：scrape→ingest→alert→notify 端到端（Telegram mock）
│   └── factories.py
├── alembic.ini  pyproject.toml  Dockerfile  docker-compose.yml
├── .env.example  .github/workflows/ci.yml  README.md
```

---

## 2. DB Schema（五表）

- **users**: id PK / email UNIQUE / hashed_password(★絕不存明碼) / telegram_chat_id NULL / is_active / created_at
- **products**（全使用者共享）: id / brand / name / category / **product_url UNIQUE(★冪等 key)** / image_url / current_sale_price / original_price / discount / last_scraped_at
- **price_history**: id / product_id FK / sale_price / discount / recorded_date / **UNIQUE(product_id, recorded_date)(★同日一筆)**
- **watchlists**: id / **user_id FK ON DELETE CASCADE** / keyword / max_price NULL(null=只要特價) / is_active / created_at
- **alerts**: id / user_id FK / watchlist_id FK / product_id FK / triggered_price / reason(at_target|price_drop) / **dedup_key UNIQUE(user_id, product_id, triggered_price)(★DB 層去重)** / is_notified / created_at

關聯：user 1—N watchlist、user 1—N alert、product 1—N price_history、product 1—N alert、watchlist 1—N alert。products/price_history 全域共享；watchlist/alert user-scoped。

---

## 3. API 端點

| Method | Path                   | 用途                                   | Auth        |
| ------ | ---------------------- | -------------------------------------- | ----------- |
| GET    | /health                | liveness/readiness                     | 否          |
| POST   | /auth/register         | 註冊                                   | 否          |
| POST   | /auth/login            | 登入→access+refresh                    | 否（★限速） |
| POST   | /auth/refresh          | refresh 換 access                      | refresh     |
| GET    | /users/me              | 取得使用者                             | ✓           |
| PATCH  | /users/me              | 更新（綁 telegram）                    | ✓           |
| GET    | /products              | 列特價（分頁/品牌/關鍵字/排序 filter） | 可選        |
| GET    | /products/{id}         | 商品詳情                               | 可選        |
| GET    | /products/{id}/history | 價格歷史（前端趨勢圖）                 | 可選        |
| GET    | /watchlist             | 我的關注                               | ✓           |
| POST   | /watchlist             | 新增關注                               | ✓           |
| PATCH  | /watchlist/{id}        | 修改                                   | ✓           |
| DELETE | /watchlist/{id}        | 刪除                                   | ✓           |
| GET    | /alerts                | 我的警示（分頁，新→舊）                | ✓           |
| POST   | /admin/scrape          | 手動觸發爬蟲（示範用，admin 限制）     | ✓           |

FastAPI 自動產 /docs + /openapi.json → README 放截圖。

---

## 4. 分階段實作（依賴 + 可逆性）

寫程式/測試/本機跑全部**可逆、自主**。需 Root 的明確標出。

- **Phase 0 鷹架**：pyproject.toml（FastAPI/SQLModel/alembic/psycopg/pydantic-settings/argon2/pyjwt/pytest/httpx/ruff）、core/config.py、.env.example（先定 env 名）。
- **Phase 1 DB 地基**：5 SQLModel models(★) → session.py + alembic init → 第一個 migration → `compose up postgres` + `alembic upgrade head` 驗證。
- **Phase 2 Auth(★核心自刻)**：security.py（hash+JWT）→ user_repo + auth_service + auth router + deps.get_current_user → test_auth（註冊→登入→帶 token→過期/竄改 401）。**補：auth 端點 rate limit。**
- **Phase 3 搬爬蟲+ingest**（大半 vibe-code）：搬 uniqlo/net 進 app/scrapers/ 抽 base.py Protocol、輸出改 DTO → ingest_service upsert products(依 url)+price_history(同日覆寫)。可與 Phase 2 並行。**補：尊重 robots.txt、禮貌限速、註明個人研究用途。**
- **Phase 4 Watchlist+Alert(★演算法自刻)**：watchlist CRUD+測試 → alert_service（搬 check_watchlist+\_prev_price，改多使用者、去重用 DB unique）。**純函式、不需 DB 即可單元測試。**
- **Phase 5 背景排程**：scheduler.py(APScheduler) + tasks.scrape_all（scrape→ingest→detect→notify_telegram）→ main.py lifespan 啟動（每日 cron）。注意：uvicorn 多 worker 會跑多份 scheduler → 單 worker 或加 job 鎖。
- **Phase 6 容器化**：Dockerfile(multi-stage/非root/healthcheck) + compose(app+postgres, depends_on healthy)。沙箱 docker 封 → Root 在本機/AWS Tokyo box 跑。
- **Phase 7 CI**：.github/workflows/ci.yml（ruff check → pytest，含 `services: postgres` + health check）。**補：可加 mypy（SQLModel 有型別，type-safety 訊號）。**
- **Phase 8 上線(★需 Root/不可逆)**：開/選雲端機（可重用 AWS Tokyo box）、買網域+DNS+HTTPS(Caddy/nginx+Let's Encrypt，花錢)、放 production secrets+Telegram token、README 補架構圖+Swagger 截圖+live demo URL。
- **Phase 9 前端 live demo(★審視補)**：frontend/ 沿用 sale-tracker React UI，改成登入後叫真 API（list products / 管 watchlist / 看 alerts）；部署成可點 URL。

順序：0 → 1 → (2 ∥ 3) → 4 → 5 → 6 → 7 → (8 需 Root) → 9。Phase 8 前全部可本機跑起整套（含 compose postgres），不依賴 Root。

---

## 5. 技術取捨（推薦）

- **SQLModel**（vs SQLAlchemy）：一個 class 兼 ORM+Pydantic schema，少一半 boilerplate；面試可說「底層就是 SQLAlchemy，複雜 query 可 drop down」。
- **APScheduler**（vs Celery）：每日批次不需 broker/worker；README 寫取捨「未來要 per-user 即時/高頻+重試+水平擴展再遷 Celery+Redis」＝展示懂何時不過度設計。
- **JWT access(15–30min)+refresh(數天)**：展示懂 token 生命週期。
- **argon2**（或 bcrypt）：能說「為何不能 MD5/SHA、為何要 salt」最重要。
- **同步先行**（psycopg3 sync）：I/O batch + 低流量，好讀好測；README 註明知道 async 路徑。

---

## 6. 自刻清單（踩雷地圖）

1. **JWT/Auth（最高優先自刻）**：雷＝secret 進版控、token 不過期、refresh/access 不分流、密碼比對非 constant-time。
2. **降價/達標演算法（差異化核心）**：搬 tracking.check_watchlist+\_prev_price；去重改 DB `UNIQUE(user_id,product_id,triggered_price)`（讓 DB 保證冪等，別在應用層維護 set）；設計成純函式（輸入 items+history+watchlist→輸出 alerts）好測。
3. **Repository 層邊界**：repo 只回 model 不含商業邏輯、service 不碰 HTTP、router 不碰 SQL。
4. **DB schema + idempotent upsert**：products.product_url unique、price_history (product_id,date) unique。
5. **測試 DB fixture**：每 test 包 transaction rollback；CI 用 GitHub Actions `services: postgres` + health check。

可放心 vibe-code：scraper 搬移、CRUD boilerplate、Dockerfile、compose、CI yaml、README 樣板。
