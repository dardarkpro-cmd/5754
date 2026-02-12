# Smart Canteen MVP

Backend (Flask) + Frontend (Vite Vanilla JS) для демо заказа еды.

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm

## Backend Setup

```powershell
cd backend

# Create venv (first time only)
python -m venv venv

# Activate venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed database
python seed.py

# Run server (http://127.0.0.1:5000)
python run.py
```

## Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Run dev server (http://localhost:5173)
npm run dev
```

## Cloudflare Tunnel (Public Access)

Для публичного доступа через Cloudflare Tunnel используйте одну ссылку на frontend.
Vite proxy автоматически проксирует `/api/*` на backend (127.0.0.1:5000).

**Порядок запуска (3 терминала):**

```powershell
# Терминал 1: Backend (запускать ПЕРВЫМ)
cd backend
.\venv\Scripts\activate
python run.py
# Работает на http://127.0.0.1:5000

# Терминал 2: Frontend (запускать ВТОРЫМ)
cd frontend
npm run dev -- --host 0.0.0.0
# Работает на http://0.0.0.0:5173

# Терминал 3: Cloudflare Tunnel (запускать ПОСЛЕДНИМ)
cloudflared tunnel --url http://127.0.0.1:5173
# Получите публичную ссылку типа https://xxx.trycloudflare.com
```

> **Важно**: 
> - Все API запросы идут через `/api/...` (относительные пути), поэтому работает через один туннель на frontend.
> - В `vite.config.js` включён `allowedHosts: true` для разрешения доступа через `*.trycloudflare.com`.

## Demo Flow (Full MVP)

Flow: Login(student1) → Menu → Cart → Checkout → Login(cook) → Cook Queue → Mark Ready → Pickup Claim

### Step 1: Student Login & Order

1. Open http://localhost:5173/#login
2. Enter Login: `student1`, PIN: `123456` → Click **Login**
3. Go to **Menu** (or open http://localhost:5173/#menu)
4. Click **Add** on some items to add them to cart
5. Go to **Cart** (or click Cart button in nav)
6. Click **Proceed to Checkout**
7. Click **Place Order & Pay**
8. Note the displayed **Order ID**

### Step 2: Cook Prepares Order

1. Click **Login** button in nav
2. Click **Logout** (if logged in)
3. Login as: `cook` / PIN: `123456`
4. Go to **Cook** page → See the order in queue
5. Click **Mark Ready** → Note the **PIN code** displayed

### Step 3: Student Picks Up Order

1. Go to **Pickup** page (http://localhost:5173/#pickup)
2. Enter **Order ID** from Step 1 (auto-filled if same session)
3. Enter **PIN code** from Step 2
4. Click **Claim with PIN**
5. ✅ Success! Order claimed.

---

## JWT Token (2 hours)

Токен живёт 2 часа. Проверить:
```powershell
# После login скопировать access_token
# Вставить на https://jwt.io
# Посмотреть exp - должен быть ~+2 часа от iat
```

## Test Accounts

| Login | PIN | Role |
|-------|-----|------|
| admin | 123456 | admin |
| cook | 123456 | cook |
| student1 | 123456 | user |
| student2 | 123456 | user |
| student3 | 123456 | user |

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /health | GET | No | Health check |
| /api/auth/login | POST | No | Login, get JWT |
| /api/menu?location_id=loc-1&date=YYYY-MM-DD | GET | Yes | Get daily menu items |
| /api/catalog?location_id=loc-1 | GET | Yes | Get all catalog items |
| /api/orders | POST | Yes | Create order |
| /api/orders/my | GET | Yes | Get current user's orders |
| /api/orders/{id} | GET | Yes | Get order details |
| /api/payments/fake | POST | Yes | Fake payment |
| /api/cook/daily-menu | GET | Yes (cook/admin) | Get daily menu structure |
| /api/cook/daily-menu | PUT | Yes (cook/admin) | Create/update daily menu |
| /api/cook/orders/queue?location_id=loc-1 | GET | Yes (cook) | Get orders queue |
| /api/cook/orders/{id}/ready | POST | Yes (cook) | Mark order ready → generates pickup_code |
| /api/pickup/claim | POST | No | Claim order with {order_id, pickup_code} |

## Pickup Code Verification (Full Flow)

### Via UI

1. Login as `student1 / 123456` → **Menu** → add items → **Checkout** → place order
2. Login as `cook / 123456` → **Cook** → see the PAID order → click **Отметить готовым**
3. Cook sees the 6-digit **Код выдачи** (e.g. `047291`)
4. Login as `student1 / 123456` → **Мои заказы** → order shows READY with the pickup code
5. Go to **Pickup** → enter Order ID + pickup code → click **Получить заказ**
6. Order status changes to PICKED_UP ✓

> After `python seed.py` there is already a sample PAID order (`order-demo-1`) for `student1`.

### Via API (PowerShell)

```powershell
# 1. Login as cook
$resp = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/auth/login -Method POST -ContentType "application/json" -Body '{"login":"cook","pin":"123456"}'
$token = $resp.access_token

# 2. Mark demo order ready (generates pickup_code)
$ready = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/cook/orders/order-demo-1/ready -Method POST -ContentType "application/json" -Headers @{Authorization="Bearer $token"} -Body '{}'
$ready  # shows pickup_code

# 3. Claim order with the code
$code = $ready.pickup_code
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/pickup/claim -Method POST -ContentType "application/json" -Body ('{"order_id":"order-demo-1","pickup_code":"' + $code + '"}')
```

## Daily Menu ("Меню дня") Verification

### Via UI

1. Login as `cook / 123456`
2. Click **Меню дня** in nav → see all catalog items with checkboxes
3. Pick a date, check/uncheck items, set stock quantities
4. Click **Сохранить** → success message
5. Login as `student1 / 123456`
6. Menu page shows items for today's daily menu; change date to see other days

### Via API (PowerShell)

```powershell
# Login as cook
$resp = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/auth/login -Method POST -ContentType "application/json" -Body '{"login":"cook","pin":"123456"}'
$token = $resp.access_token

# Get catalog
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/catalog?location_id=loc-1" -Headers @{Authorization="Bearer $token"}

# Get daily menu for today
$today = (Get-Date).ToString("yyyy-MM-dd")
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/cook/daily-menu?location_id=loc-1&date=$today&meal_slot=lunch" -Headers @{Authorization="Bearer $token"}

# Save daily menu
$body = '{"location_id":"loc-1","menu_date":"' + $today + '","meal_slot":"lunch","items":[{"menu_item_id":"item-1","stock_qty":10,"is_available":true},{"menu_item_id":"item-3","stock_qty":20,"is_available":true}]}'
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/cook/daily-menu" -Method PUT -ContentType "application/json" -Headers @{Authorization="Bearer $token"} -Body $body

# Check user-facing menu
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/menu?location_id=loc-1&date=$today" -Headers @{Authorization="Bearer $token"}
```
