# Verification report

Verified on 3 October 2026 in the user's Windows workspace.

## Completed checks

- Django configuration check and committed migrations applied to isolated MySQL 8.0.43 at 127.0.0.1:3307.
- MySQL backend tests covering registration, duplicate email/register number, password hashing, login, refresh rotation/blacklist, logout, role escalation protection, admin permissions, ownership, status sequence, future-date rejection, preview side effects, issuance, duplicate prevention, PDF download, public privacy, pronouns/escaping, revocation, rollback, filters, final-data validation, invalid logout tokens, and simultaneous issuance.
- Frontend ESLint check and Vite production build.
- npm dependency audit reported zero vulnerabilities at install time.
- Chrome browser workflow: register Kaviya, login, pending dashboard, logout, admin login, search, correct name, mark In Progress and Completed, preview, confirm issuance, logout, student login, download, verify by token and ID, refresh an invalid access token, revoke, and verify Revoked without a green success state.
- Chrome public-page checks: desktop/mobile layouts, no horizontal overflow at 390 px, mobile navigation, registration page, invalid certificate ID, and camera permission-denied feedback.
- QR parser rejects external domains, JavaScript URLs, malformed tokens, credentials, and query-string redirects.
- Actual html5-qrcode camera decoding: extracted the QR image from the downloaded ReportLab PDF, placed it in a simulated Chrome camera stream, and confirmed navigation to the matching revoked certificate.
- PDF inspection: one A4 page, correct dynamic student/project/dates and female wording, no old reference candidate/project, visible QR and certificate ID, clear director section, and no visible overlaps or clipping.
- Visual review of desktop home, mobile home, admin dashboard, student dashboard, and revoked mobile result. Decorative icons were removed from accessible names and mobile gutters adjusted after the first review.

## Limits of verification

- A physical webcam/phone was not used. The real decoder was tested with a simulated camera; actual device permission, focus, and lighting still require a device check.
- Physical bond-sheet printer registration/offsets were not calibrated.
- The reference DOCX was inspected through its exact OOXML dimensions, fonts, margins, paragraphs, and positioning. No Word/LibreOffice renderer was available for a pixel-by-pixel comparison with the original DOCX.
- The local application was tested on MySQL, not a deployed multiworker production server. Production hosting, TLS, shared-cache throttling, and backups remain operational setup.
- No handwritten signature image was supplied; no signature was invented.

Screenshots in `docs/qa` are development evidence. The issued test certificate was deliberately revoked as part of the workflow and is not a real internship credential. Downloaded test PDFs and camera fixtures are kept in the task's private work directory, not in the source archive.
