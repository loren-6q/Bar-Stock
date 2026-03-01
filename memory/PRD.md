# Bar Stock Manager - PRD

## Problem Statement
Full-stack bar stock management application with mobile-friendly stock counting, editable inventory, automated shopping list generation, purchase confirmation workflow, and historical analysis reports.

## Architecture
- **Frontend**: React (single App.js), Tailwind CSS, Shadcn UI, Axios
- **Backend**: FastAPI, Pydantic, Motor (async MongoDB)
- **Database**: MongoDB (Atlas)

## 5-Tab Workflow
1. **COUNT** - Mobile-friendly stock counting by location (Bar, Beer, Lobby, Storage)
2. **INVENTORY** - Full inventory view with Have/Cases/Target/Need/Order columns
3. **ORDERS** - Orders grouped by supplier with Copy & Confirm Purchase workflow
4. **MANAGE** - Spreadsheet-style item management with inline editing, grouping, filtering
5. **ACCOUNTING** - Saved stock sessions with view details dialog, usage analysis (coming soon)

## DB Schema
- **items**: `{id, name, category, category_name, sub_category, units_per_case, cost_per_unit, cost_per_case, sale_price, target_stock, bought_by_case, primary_supplier, sort_order}`
- **stock_counts**: `{id, item_id, main_bar, beer_bar, lobby, storage_room, total_count, count_date}`
- **stock_sessions**: `{id, session_name, session_date, is_active, session_type}`
- **historical_counts**: `{session_id, item_id, main_bar, beer_bar, lobby, storage_room, total_count}`
- **confirmed_orders**: `{id, supplier, status, completed_at, items[]}`

## What's Been Implemented
- [x] 5-tab workflow (COUNT, INVENTORY, ORDERS, MANAGE, ACCOUNTING)
- [x] Mobile-friendly stock counting with case/unit toggle
- [x] Inventory table with order quantity editing
- [x] Orders grouped by supplier with Copy and Confirm Purchase
- [x] Spreadsheet-style MANAGE tab with inline editing
- [x] Sub-category grouping (nested under parent category)
- [x] Sale Price column in MANAGE tab
- [x] Local edit state for inputs (prevents re-sort while typing)
- [x] ACCOUNTING tab session view dialog
- [x] Price list feature
- [x] Data loss protection on initialize-real-data endpoint
- [x] localStorage persistence for order quantities and case modes

## Completed - Feb 2026
- Fixed ACCOUNTING tab: sessions now clickable with detailed view dialog
- Fixed MANAGE tab sub-category input bug (local state prevents re-sorting)
- Added Sale Price column to MANAGE tab and backend Item model
- Improved sub-category grouping (parent header + indented sub-labels)
- Unit price auto-calculation now rounds to 1 decimal place
- Sub-category reordering via up/down arrows in MANAGE tab (persists across all tabs)

## Backlog
- P2: Full Accounting/Reporting (usage & cost analysis between counts)
- P2: Complete data import (user needs to re-enter missing items manually)
- P3: Revenue tracking/estimation
- P3: Quick end-of-night stock checks
