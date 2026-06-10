# Smart Asset Management & Resource Allocation Platform (SAMRAP)
## Implementation Checklist & Serial Tasks (Django Version)

This document contains the step-by-step tasks required to implement the asset management platform. Each task depends on the preceding scaffolding and backend models.

---

### Phase 1: Project Scaffolding & Configuration
- [ ] **Task 1.1: Django Project Init**
  - Initialize Django project (named `samrap`) and default application (`inventory`) in the root workspace.
  - Setup basic settings (Timezone to local, database file to `db.sqlite3`).
- [ ] **Task 1.2: Models & Custom User**
  - Implement Custom User model inheriting from `AbstractUser` to support roles (`ADMIN`, `USER`).
  - Write models for Category, Asset, Booking, AssetHealth, and AuditLog in `models.py`.
  - Configure `AUTH_USER_MODEL` in `settings.py`.
  - Run `makemigrations` and `migrate` to set up SQLite.
- [ ] **Task 1.3: Static Assets & CSS Scaffolding**
  - Configure static files directories in Django settings.
  - Create global custom stylesheets (defining CSS custom variables for the premium dark theme colors, animations, glassmorphism filters, and layouts).
  - Scaffold `base.html` template file with responsive wrapper and navigation sidebar structure.

---

### Phase 2: Authentication & Security
- [ ] **Task 2.1: Authentication Views**
  - Set up authentication views for login, logout, and registration using Django's built-in auth views or custom views.
- [ ] **Task 2.2: Login and Registration Pages**
  - Build a high-aesthetic authentication interface featuring subtle gradients, input focus animations, and error popups.
- [ ] **Task 2.3: Session Middleware & Access Control**
  - Implement decorators or middleware to restrict routes by role (`ADMIN` vs `USER`).

---

### Phase 3: Inventory & Category Management
- [ ] **Task 3.1: Category and Asset Views**
  - Write Django views and forms to manage categories and assets (List, Create, Update, Delete).
- [ ] **Task 3.2: Seed Script / Management Command**
  - Create custom Django management command `seed_inventory` containing default categories (Cameras, Audio, Costumes, Lighting, Props) and sample items.
- [ ] **Task 3.3: Admin Inventory Interface**
  - Implement a premium data table/card grid for admins to manage stock, categories, statuses, and descriptions.

---

### Phase 4: Discovery, Search, and Booking Request Engine
- [ ] **Task 4.1: Booking View with Overlap Validation**
  - Build the booking request view using database transaction (`transaction.atomic`) and row-locking (`select_for_update`). Ensure it locks the target asset and checks overlaps in active ranges before saving.
- [ ] **Task 4.2: Asset Discovery Catalog**
  - Create a card view for users to search, filter by category, and view real-time available quantities.
- [ ] **Task 4.3: Booking Form & Inline Calendar**
  - Create an interactive form/modal displaying asset availability calendar or dates and allowing users to select duration and quantities.

---

### Phase 5: Admin Approvals & Asset Lifecycle Workflows
- [ ] **Task 5.1: Admin Approvals Dashboard**
  - Build a request-review interface where admins can approve/reject pending requests with notes.
- [ ] **Task 5.2: User Requests & Borrowing History**
  - Create a dashboard for general users to track booking request statuses (`Pending`, `Approved`, `Rejected`, `Issued`, `Overdue`, `Returned`).
- [ ] **Task 5.3: Asset Issuance & Returns (Check-out/Check-in)**
  - Create a portal for admins to record when approved assets are physically checked out (changing status to `Issued`) and returned (marking as `Returned`).

---

### Phase 6: Analytics, QR Operations & Audit Logs (Bonus Deliverables)
- [ ] **Task 6.1: Analytics View**
  - Write Django view executing database aggregates returning asset utilization percentages, categories distribution, and overdue rates.
- [ ] **Task 6.2: Analytics Dashboard UI**
  - Build a visual dashboard using Chart.js inside canvas element rendering dynamic charts and performance metric cards.
- [ ] **Task 6.3: Audit Log Recorder**
  - Create signals (`post_save`/`post_delete`) or middleware service utility logging changes (e.g., asset creation, quantity edits, manual status updates) and a dashboard to review logs.
- [ ] **Task 6.4: QR Code Utilities**
  - Add views utilizing Python's `qrcode` package to render Asset details into QR code SVG formats. Build a simulation scanner on the admin dashboard.
- [ ] **Task 6.5: Asset Health Tracker**
  - Add damage reporting and maintenance history views, enabling logs of asset conditions.

---

### Phase 7: Deployment, Testing & Verification
- [ ] **Task 7.1: Automated Integration Tests**
  - Write test suites using Django `TestCase` validating auth paths, double-booking prevention logic, and state changes.
- [ ] **Task 7.2: Containerizing with Docker**
  - Create the `Dockerfile` and `docker-compose.yml` to package Django and SQLite. Run verify commands to ensure replication works out of the box.
- [ ] **Task 7.3: Project Documentation (README & Design Doc)**
  - Compose a detailed README.md matching requirements and compile the design details into the final PDF format.
