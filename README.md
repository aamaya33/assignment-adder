I put my syllabus in, it populates my google calendar for me :)

Goal

Upload a schedule (CSV or PDF), parse into a canonical course/meeting model, generate recurring events, and sync to a selected Google Calendar idempotently.
Proposed stack (confirm preference)

Option A (Node/TypeScript): Fastify/Express, rrule, googleapis, Prisma + SQLite/Postgres.
Option B (Python): FastAPI, dateutil/rrule, google-api-python-client, SQLModel/SQLAlchemy + SQLite/Postgres.
Storage: start with SQLite, move to Postgres when deploying.
Containerize with Docker; env via .env.
Core components

Auth/Google Calendar integration
OAuth2 with offline access; store encrypted refresh token.
Scopes: https://www.googleapis.com/auth/calendar.
Target calendar selection (existing or create new).
File ingestion
POST file upload (multipart).
Validate size/type; antivirus scan optional; do not persist raw files longer than needed.

Parsing service
CSV: delimiter detection, header mapping, column-mapper fallback UI (or config).
PDF: text extraction (pdf-parse/pdfjs or pdfplumber); table extraction (Camelot/Tabula). OCR (Tesseract) for scanned PDFs.
Heuristic patterns per school; allow user to confirm column mapping.

Normalizer
Canonical model: Course, MeetingPattern (daysOfWeek, startTime, endTime, startDate, endDate, location, notes), exceptions/holidays.

Recurrence engine
Build RRULEs (WEEKLY;BYDAY=...), timezone-aware; EXDATE for holidays/breaks; handle odd/even weeks; first/last occurrence alignment.

Calendar sync service
Create/update/delete events; set reminders; location; description; color.
Idempotency via extendedProperties.private.externalId and a local event_map.
Dry-run mode; conflict detection/reporting; rate-limit/backoff.

API (minimal)
POST /imports: upload file, returns importId + parsed summary (dry-run by default).
GET /imports/{id}: parsed data, issues, mapping hints.
POST /imports/{id}/confirm: persist and sync to Google Calendar.
GET /calendars: list user calendars.
POST /calendars: create/select target calendar.

Data model (sketch)
users(id, google_user_id, email)
oauth_tokens(user_id, access_token, refresh_token, expiry, scopes, enc_salt)
calendars(id, user_id, google_calendar_id, name)
imports(id, user_id, source_type[csv|pdf], status, tz, created_at)
courses(id, import_id, name, code, section, instructor)
meetings(id, course_id, days_of_week, start_time, end_time, start_date, end_date, location, notes)
exceptions(id, meeting_id, date, reason)
event_map(id, meeting_id, google_event_id, external_id, last_synced_at)

Validation and UX
Timezone selection; semester start/end dates; holiday list upload or auto-fetch.
Column mapping UI spec (server supports schema introspection).
Report parsing warnings (e.g., ambiguous times, missing dates).

Security/compliance
Encrypt tokens at rest; rotate refresh tokens; least-privilege scopes.
File scanning, size/type limits; delete raw files after parse.
Structured logs, no PII in logs.

Testing
Unit: CSV/PDF parsers with sample fixtures.
Property tests for recurrence alignment and EXDATE correctness.
Integration: sandbox Google account; idempotent sync; DST edge cases.

Deployment
Dev: .env + SQLite.
Prod: Postgres, Docker, HTTPS, a secret manager.
CI: lint, tests, type-check; sample fixtures regression.
Milestones

Skeleton API + Google OAuth + list calendars (1–2 days)
CSV parser + column mapping + dry-run preview (2–3 days)
Recurrence/EXDATE engine + Google sync idempotency (2–3 days)
PDF text/table extraction + mapping heuristics + OCR fallback (3–5 days)
Polishing: errors, logs, tests, holiday exceptions, CLI (2–3 days)
Nice-to-haves

ICS export/import fallback.
Webhook push notifications (watch) to detect external edits.
CLI: import and sync from local files.