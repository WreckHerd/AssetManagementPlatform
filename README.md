# Smart Asset Management & Resource Allocation Platform (SAMRAP)

SAMRAP is a general-purpose, full-stack, premium-aesthetic asset management and resource allocation web application designed specifically to solve inventory tracking, booking coordination, and lending workflows for organizations, clubs, events, and resource-sharing councils.

---

---

## Demonstration Video

👉 **[Watch the Demonstration Video on YouTube](https://youtu.be/Zej2gloxwcI)**

---
## See design_document.pdf above 

##  Key Features

*   **Secure Authentication & RBAC:** Session-based authentication with distinct dashboards and route permissions for `ADMIN` and `USER` roles. Users can select their roles upon sign-up (dev-friendly simulation).
*   **Asset Discovery Catalog:** Real-time search and category filtering of assets (DSLR cameras, lights, mics, costumes, stage props). It displays live availability status and quantities.
*   **Transaction-Safe Booking Engine:** Double-booking prevention algorithm using database transactions (`transaction.atomic`) and row-locking (`select_for_update`). It calculates overlapping timelines to prevent stock over-allocations.
*   **Approvals & Issuance Workflow:** Admins can review, approve, or reject booking requests with comments. Approved requests can be checked out (issued) and checked back in (returned) with automated inventory adjustment.
*   **Asset Health & Condition Tracking:** Logs condition states (Good, Fair, Damaged, Unusable) and notes during check-ins to maintain individual asset lifecycle health.
*   **Audit Logging Ledger:** Automated system log tracking critical operations (asset creation, updates, deletions, and approval transitions) to maintain accountability.
*   **Simulated QR Code Operations:** Automatically generates QR codes for assets. Includes a simulated camera scanner page where admins can scan QR tags to instantly perform quick check-outs or check-ins.
*   **Operational Analytics:** Interactive charts (rendered using Chart.js) mapping category distribution, high-demand assets, and weekly booking rates.

---

## Technology Stack

*   **Backend & Frontend:** Django (Python 3.10+) utilizing class-based views, forms, and the built-in templating engine.
*   **Database:** SQLite — portable, relational database file (`db.sqlite3`) supporting foreign key integrity and transactional locking.
*   **Styling:** Vanilla CSS — custom designed with CSS variables to establish a modern, sleek, dark-themed glassmorphism interface (featuring Outfit and Plus Jakarta Sans typography).
*   **Icons:** Lucide Icons.
*   **Visualization:** Chart.js (included via lightweight CDN integration).
*   **QR Generation:** `qrcode` python library.
*   **Server/Containerization:** Gunicorn, Docker & Docker Compose.

---

## Setup & Installation

### Option A: Running Locally (Recommended)

1.  **Clone the Repository & Navigate to Workspace:**
    ```bash
    git clone <repository_url>
    cd AssetManagementPlatform
    ```

2.  **Create & Activate Virtual Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run Migrations:**
    ```bash
    python manage.py migrate
    ```

5.  **Seed Database (Creates Admin, User, and default assets):**
    ```bash
    python manage.py seed_inventory
    ```
    *   *Default Admin:* username: `admin` | password: `adminpass` | email: `admin@example.com`
    *   *Default User:* username: `user` | password: `userpass` | email: `user@example.com`

6.  **Run Development Server:**
    ```bash
    python manage.py runserver
    ```
    Access the application at: **`http://127.0.0.1:8000/`**

---

### Option B: Running with Docker (Containerized)

1.  **Build and Start Containers:**
    ```bash
    docker-compose up --build
    ```

2.  **Run Seeding (inside running web container):**
    ```bash
    docker-compose exec web python manage.py seed_inventory
    ```
    Access the application at: **`http://localhost:8000/`**

---

## Running Automated Tests

Run the test suite covering authentication paths, role-based access rules, check-out/check-in states, and overlap booking validation logic:
```bash
python manage.py test
```



## Project Structure

```text
├── Dockerfile                  # Production container packaging
├── docker-compose.yml          # Container configuration
├── requirements.txt            # Python dependencies
├── manage.py                   # Django CLI
├── samrap/                     # Project configuration directory
│   ├── settings.py             # Settings, DB configurations & static paths
│   └── urls.py                 # Root URL router
├── inventory/                  # Core application app
│   ├── models.py               # Custom User, Asset, Booking, Health models
│   ├── views.py                # Authentication, scan simulation & booking views
│   ├── forms.py                # Form validation for asset modifications & requests
│   └── urls.py                 # App sub-routing patterns
├── static/                     # Static assets directory
│   └── css/
│       └── styles.css          # Core dark-theme stylesheets
└── templates/                  # Base and application HTML templates
    ├── base.html               # Navigation shell & global layouts
    └── inventory/              # View templates (Dashboard, Catalog, Analytics)
```
