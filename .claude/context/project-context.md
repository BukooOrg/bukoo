# Project Context — Bukoo Bookstore E-commerce System

Read this for high-level orientation: what the system does, who uses it, what
features must be built, and which external providers are in play.

---

## Project Summary

| Category | Details |
|----------|---------|
| **Name** | Bukoo — Bookstore E-commerce System |
| **Objective** | Web-based bookstore for browsing, searching, and purchasing books. Includes secure authentication, admin dashboard for inventory/order management. Focus on UX, data security, scalability, and maintainability. |
| **Primary Users** | Customers and Admins |
| **Supported Platforms** | Windows 11+ and Linux |
| **Browser Support** | Google Chrome, Microsoft Edge, Mozilla Firefox |

## Out of Scope

- Localization / multi-language (English and Malay only)
- Real financial transactions — payments are **simulated** (success/failure only)
- Physical logistics and shipping — no courier integration
- Vendor marketplace — single-seller store only

---

## Feature List

### Customer Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Login** | Securely access user account |
| 2 | **Logout** | Securely exit user account |
| 3 | **Account Registration** | New user creates an account to access personalized features |
| 4 | **Account Deletion** | User permanently deletes their profile and personal data |
| 5 | **Password Recovery/Reset** | Verify credentials (name + date of birth), set a new password |
| 6 | **Manage Profile** | Update personal details, contact info, password, and shipping address |
| 7 | **Browse Book Catalog** | View the list of available books |
| 8 | **Search and Filter Books** | Advanced search and category filtering to find specific titles |
| 9 | **View Book Details** | Retrieve and display full information about a book |
| 10 | **Manage Shopping Cart** | Add, remove, or update quantities of books in the cart |
| 11 | **Checkout Order** | Proceed to simulated payment and confirm the purchase |
| 12 | **View Order History** | Track previous purchases and current order status |
| 13 | **Submit Rating and Review** | Provide written feedback and star rating for purchased books |
| 14 | **Manage Wishlist** | Save books for future purchase; encourages return visits |

### Admin Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Add New Book** | Register a new book into the system database |
| 2 | **Update Book Information** | Modify the details of an existing book record |
| 3 | **Remove Book** | Remove a book from the active inventory (soft-delete) |
| 4 | **Update Stock Levels** | Adjust the physical count of books available for sale |
| 5 | **Monitor Inventory Dashboard** | View live metrics on stock status and product performance |
| 6 | **Generate Sales and Analytics Reports** | Export data (PDF/CSV) for revenue, top-selling authors, monthly volume |
| 7 | **Manage Orders** | Review customer orders; update fulfillment status (Pending → Shipped → Delivered) |
| 8 | **View and Moderate Reviews** | Read customer reviews; hide or delete spam, inappropriate, or spoiler content |
| 9 | **Manage Categories and Genres** | Create, rename, or delete genres; ensure books are never assigned non-existent categories |
| 10 | **Account Management** | View user profiles, manually reset passwords, suspend/deactivate accounts, register new admin accounts |

---

## External Infrastructure and Providers

| Concern | Dev | Production |
|---------|-----|-----------|
| **Database** | PostgreSQL + pgAdmin UI | PostgreSQL |
| **Object storage** | MinIO (local S3-compatible) | AWS S3 |
| **Email sending** | Mailpit (SMTP trap, UI at `:8025`) | TBD |
| **Background jobs** | Celery + Redis broker + Flower monitor + Kombu | Same |
| **OAuth** | Google OAuth | Google OAuth |
| **Payment** | Simulated only (no real provider) | Simulated only |

---

## System Boundaries

- **Frontend** — React web portal for both customers and admins
- **Backend** — FastAPI server handling business rules, validation, and queries
- **Database** — PostgreSQL for persistent storage of books, users, orders
- **Object Storage** — MinIO (dev) / S3 (prod) for book cover images and other assets

---

## Implementation Status (as of project start)

**Implemented:**
- User registration, credential login, Google OAuth login
- JWT authentication with Bearer token guard
- Health check endpoint
- Domain entities for all 18 types (User, Book, Order, Cart, Wishlist, etc.)
- ORM models and mappers for all entities
- Celery + Redis task queue with email notification service
- MinIO / S3 storage abstraction

**Not yet implemented (use cases to build):**
- All customer use cases beyond auth (browse, search, cart, checkout, orders, reviews, wishlist, profile management, password reset, account deletion)
- All admin use cases (book management, inventory dashboard, order management, review moderation, category management, analytics reports, user account management)
- Frontend pages beyond: Home, Shop, ProductDetail, Login, Register
