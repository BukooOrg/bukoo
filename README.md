# Bukoo Ecommerce Platform

A premium, editorial-minimalism bookstore ecommerce application built with React (Vite) and FastAPI.

## Project Structure

- `/src`: Frontend application (React + Vite + Tailwind CSS)
- `/backend`: Backend API (FastAPI + SQLAlchemy + PostgreSQL)
- `docker-compose.yml`: Database configuration (PostgreSQL)

---

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.9+)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for the database)

# ❗❗❗❗❗Dont do 1 and 2 first, unfinished ❗❗❗❗❗

### 1. Database Setup

The project uses PostgreSQL. The easiest way to run it is via Docker:

```bash
docker-compose up -d
```

This will start a PostgreSQL instance on `localhost:5432`.

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update `DATABASE_URL` if necessary.
5. Seed the database (optional but recommended for testing):
   ```bash
   python -m app.seed
   ```
6. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

### 3. Frontend Setup

1. Navigate to the root directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.

---

## Testing

### Backend Testing
To run backend tests (if available), ensure your virtual environment is active and run:
```bash
pytest
```

### Frontend Testing
To run the frontend dev server and verify UI:
```bash
npm run dev
```
Check the console for any linting or build errors:
```bash
npm run lint
```

## Technologies Used

- **Frontend**: React, Vite, Tailwind CSS, Framer Motion, Radix UI, Lucide Icons.
- **Backend**: FastAPI, SQLAlchemy, Pydantic, Alembic.
- **Database**: PostgreSQL.
- **Design**: Premium, quiet-luxury aesthetic with editorial focus.
