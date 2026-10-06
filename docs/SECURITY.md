# Security Architecture & Hardening Document

## 1. Secret & Credential Governance
- Database credentials and application secrets are stored exclusively in environment variables (`.env`).
- `.env`, `.env.production`, and local SQLite database files are excluded from Git via `.gitignore`.
- Repository audited for hardcoded API keys, tokens, or private keys; zero real secrets found.

## 2. Network Isolation & Port Security
- PostgreSQL container port 5432 is kept strictly within the internal Docker network in `docker-compose.prod.yml`.
- Nginx acts as the single public entry point on port 80/443.

## 3. Container Security & Non-Root Execution
- Backend container runs under dedicated system user `appuser`.
- Next.js frontend container runs under dedicated system user `nextjs` (UID 1001).

## 4. HTTP Security Headers
Nginx enforces:
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy`: Restricts inline script execution and external domain calls.

## 5. Input Validation & Bounds Checking
- Pydantic schemas enforce bounds validation:
  - Latitude $\in [-90, 90]$
  - Longitude $\in [-180, 180]$
  - Distance $> 0$, Weight $> 0$
