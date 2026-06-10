# Smart Asset Management & Resource Allocation Platform (SAMRAP)
## Design & Requirements Document (DRD)

---

## 1. Introduction & Project Overview
The **Smart Asset Management & Resource Allocation Platform (SAMRAP)** is a full-stack web application designed to solve resource coordination, inventory tracking, and allocation challenges. Specifically modeled for the **Cultural Council of IIT Roorkee**, SAMRAP centralizes the management of high-value shared resources—such as DSLR cameras, studio lighting equipment, audio systems, costumes, stage props, recording gear, and event infrastructure.

By replacing fragmented manual logs, spreadsheets, and informal communication channels, SAMRAP ensures real-time operational visibility, prevents scheduling conflicts, and tracks utilization metrics dynamically.

---

## 2. Core Problem & User Personas

### 2.1 The Problem
Shared assets are frequently booked across multiple council sections and events. Without a centralized system, the organization suffers from:
*   **Double-bookings / Scheduling conflicts:** Multiple groups requesting the same asset simultaneously.
*   **Lack of Accountability:** No clear record of who has an asset, its condition, and when it is due.
*   **Inventory Underutilization:** Assets sitting idle because sections don't know they are available.
*   **Operational Inefficiencies:** Excessive manual coordination to approve, issue, and return assets.

### 2.2 Target User Personas
*   **Resource Consumers (General Users / Council Members):**
    *   Need to quickly browse available assets.
    *   Need to filter by category, check real-time availability, and request bookings for specific time slots.
    *   Want to track the progress of their requests and see their personal borrowing history.
*   **System Administrators (Council Admins / Equipment Managers):**
    *   Need complete control over inventory (add, edit, categorize, archive assets).
    *   Need an approval interface to review, approve, or reject booking requests.
    *   Need to manage the physical issuance and return of assets, logging conditions and deadlines.
    *   Want high-level operational analytics to plan inventory expansion or maintenance.

---

## 3. Product Features & "The What"

### 3.1 Mandatory Feature Requirements

#### A. Secure User Authentication
*   **User Registration & Login:** Email-password or username-password authentication.
*   **Role-Based Access Control (RBAC):** Distinct interfaces and permissions for `ADMIN` and `USER` roles.
*   **Session Management:** Secure session-based authentication (using Django's built-in session engine).

#### B. Inventory Management (Admin Only)
*   **CRUD Operations:** Ability to add, view, update details of, and delete/archive assets.
*   **Asset Schema Attributes:**
    *   *Name:* Unique identifier (e.g., "Sony Alpha 7 IV DSLR").
    *   *Category:* Grouping (e.g., Cameras, Lighting, Audio, Costumes).
    *   *Description:* Usage guidelines, model specs.
    *   *Quantity Available:* Total owned vs current free count.
    *   *Status:* Ready, In Maintenance, Damaged, Retired.
*   **Categorization & Tagging:** Dynamic creation/assignment of asset categories.

#### C. Asset Discovery & Booking (User & Admin)
*   **Search & Filtering:** Real-time search by name, description, and filter by category or availability status.
*   **Availability Checker:** A visual calendar or timeline displaying dates when an asset is reserved.
*   **Booking Request Engine:**
    *   Users submit requests specifying asset, quantity, start date, and end date.
    *   **Inventory Protection:** The system MUST mathematically prevent bookings that exceed the physical quantity owned during that specific duration.

#### D. Approval Workflow (Admin & User)
*   **Admin Request Manager:** Dashboard listing pending bookings. Admins can `Approve` or `Reject` with comments.
*   **User Request Tracker:** Live updates showing whether a request is `Pending`, `Approved`, `Rejected`, `Issued`, or `Returned`.

#### E. Asset Issue & Return Management (Admin Only)
*   **Physical Issuance (Check-out):** When a user picks up an approved asset, the Admin updates status to `Issued`, which decrements available count.
*   **Return Tracking (Check-in):** On return, Admin checks asset back in, restoring inventory counts and recording returning condition.
*   **Due Date Management:** Highlighting overdue assets, calculating delays, and setting return policies.

#### F. Analytics Dashboard (Admin Only)
*   **Utilization Rates:** Percentage of time assets are booked vs idle.
*   **High-Demand Items:** Rankings of most booked assets.
*   **Active vs Overdue Metrics:** Quick visual status cards.
*   **Interactive Visualizations:** Sleek charts (Bar, Pie, Line) representing allocation metrics.

#### G. Borrowing History (User & Admin)
*   **User Log:** Personal log of all past bookings, status history, and dates.
*   **Admin Log:** Global activity ledger showing historical actions by all users and admins.

---

### 3.2 Optional & Bonus Features (Out of Scope / Skipped)
*   **Notification System:** *SKIPPED (Per user instruction)*

### 3.3 Active Optional & Bonus Features
*   **Audit Logs:** Track important actions such as asset creation, inventory updates, booking approvals, and returns.
*   **QR Code-Based Asset Operations:** Generate QR codes for assets and scan assets during check-out and check-in (simulated scanner).
*   **Asset Health & Condition Tracking:** Track condition logs, damage reports, and maintenance history.
*   **Dockerized Deployment:** Provide a containerized development environment using Docker and Docker Compose.

---

## 4. User Experience & Design Guidelines

To create a **premium, modern, and visually stunning application**, the interface must feel alive and high-end:
1.  **Color Palette:** Sleek dark-theme default with deep blues (`#0B132B`), charcoal (`#1C2541`), highlighted by vibrant cyan/teal accents (`#48CAE4`, `#00B4D8`) and semantic alerts (success: emerald, warning: amber, danger: rose).
2.  **Typography:** Modern typography using clean sans-serif typefaces (e.g., Google Fonts' **Inter** or **Outfit**).
3.  **Glassmorphism & Shadows:** Soft card borders, subtle background blurs (`backdrop-filter: blur()`), and layered drop shadows to suggest depth.
4.  **Micro-animations & Interactive States:**
    *   Smooth transitions for button hovers, input focuses, and modal popups.
    *   Loading state skeletons rather than blank screens.
    *   Hover scale effects on asset listing cards.
5.  **Responsive Layout:** Desktop-first dashboard with mobile-friendly collapsible menus and responsive tables.

---

## 5. Final Criteria for Success (Validation Rules)

To declare this project successfully completed, the following metrics must be satisfied:

| Metric | Target / Requirement | Verification Method |
| :--- | :--- | :--- |
| **Authentication Security** | Access cookie validated on each private route. Unauthorized view access blocked. Redirects to login. | Django test client & manual verification |
| **Inventory Validation** | Booking requests exceeding stock levels for overlapping periods are strictly rejected. | Django TestCase validation |
| **Status Integrity** | Asset counts increment/decrement automatically across booking, issuance, and return phases. | Database transaction state validation |
| **Analytics Dashboard** | Live, dynamic updates rendering usage charts using mock or real inventory logs. | Visual inspection / Chart.js integration |
| **UI Aesthetics** | No plain browser defaults. Premium dark mode theme with cohesive CSS variables. | UI Walkthrough & Chrome Inspector check |
| **Docker Build** | Single-command launch via `docker-compose up` builds and runs the platform locally. | Terminal test command |
| **Code Quality** | Clean code with zero console/lint errors, modular templates, and solid error handling. | Linter execution / python -m py_compile |
| **Documentation** | DB mapping, ERD representation, and setup instructions complete. | Verification of PDF & README |
