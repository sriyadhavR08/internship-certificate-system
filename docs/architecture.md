# Architecture and API

The browser calls DRF with JWT access tokens. DRF checks role and ownership before loading private data. MySQL stores users, profiles, one internship per student, a yearly sequence, and at most one certificate per internship. PDF files are stored privately through Django FileField.

Issuance locks the internship row, checks completion and absence of an existing certificate, locks/increments the current year's sequence, snapshots the details, generates the PDF/QR, saves the file/record, and changes status within one transaction. Failures remove newly saved files and roll back database changes. Database uniqueness protects both the visible certificate ID and random token. A process crash between file storage and DB commit could leave an unreferenced file; periodic storage reconciliation is an operational improvement.

The reference DOCX contains no embedded logo, border, or signature. It uses A4 portrait (11906×16838 twips), 1440-twip margins, Times New Roman, a centered bold 16 pt heading, justified 14 pt body with half-inch first-line indents, left date/location, and a right-aligned director section. The supplied master wording replaces the old candidate/project/dates. The digital layout adds the real logo in the reference's upper blank region and a QR/ID in the lower margin region.

## API routes

All paths are under `/api/`. Standard data reads return JSON directly; action and error responses include human-readable messages where useful. DRF validation errors are wrapped as `success: false`, `message`, and `errors`. JWT endpoints follow SimpleJWT's token response format. Preview/download endpoints return PDF bytes.

| Method | Path | Access |
|---|---|---|
| POST | auth/register/ | Public; always creates Student |
| POST | auth/login/ | Public; email/password |
| POST | auth/token/refresh/ | Valid refresh token |
| POST | auth/logout/ | Authenticated owner of refresh token |
| GET | auth/me/ | Authenticated |
| GET | student/profile/ | Student's own full record |
| GET | student/internship/ | Student's own full record |
| GET | student/certificate/ | Student's own certificate metadata or null |
| GET | admin/dashboard/ | Admin summary and recent activity |
| GET | admin/students/ | Admin; search/project/status/start/end/page |
| GET, PUT | admin/students/{user_id}/ | Admin view/correct details before issuance |
| PATCH | admin/internships/{id}/status/ | Admin; `{status: IN_PROGRESS or COMPLETED}` |
| GET | admin/certificates/preview/{internship_id}/ | Admin; PDF, no issuance side effects |
| POST | admin/certificates/generate/{internship_id}/ | Admin; requires Completed |
| GET | admin/certificates/ | Admin; search/status/page |
| PATCH | admin/certificates/{id}/revoke/ | Admin; idempotent revocation |
| GET | certificates/{id}/download/ | Owner/admin; valid certificates only |
| GET | public/verify/token/{token}/ | Public whitelist of certificate fields |
| GET | public/verify/id/{certificate_id}/ | Public whitelist of certificate fields |

Pagination returns `{count, page, results}` with 20 records per page. Admin date filters match the exact start/end date; project filtering matches the exact project name. Student correction uses all editable fields (PUT), not partial data.

The certificate token appears only where needed to build the owner's/admin's verification link and the QR. Public verification responses do not echo it. Public endpoints ignore stale Authorization headers, so an expired login does not prevent verification.

## Scope decisions

- One internship per student account, matching the registration workflow. Multiple internships per account require a separate enrollment UI.
- Issued data is immutable. Revoke is supported; replacement certificates are not yet a business workflow.
- Admin preview can inspect any registered student's details but generation requires Completed.
- Inclusive calendar-month duration resolves the one-month September example in the specification.
- Django Admin's profile/internship/certificate records are read-only, so operators use the React workflow instead of bypassing state transitions.
- No email delivery, password-reset mailer, digital signing certificate, or external hosting was specified or configured.
