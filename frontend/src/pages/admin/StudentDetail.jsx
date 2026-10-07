import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, errorText, pdfBlob, resolveMediaUrl } from "../../services/api";
import { Loading, Notice, Status, Confirm } from "../../components/Common";
import StudentFields from "../../components/StudentFields";
import CertificateActions from "../../components/CertificateActions";

export default function StudentDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null),
    [values, setValues] = useState({}),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false),
    [editing, setEditing] = useState(false),
    [preview, setPreview] = useState(""),
    [confirm, setConfirm] = useState(false),
    [endDateInput, setEndDateInput] = useState(""),
    [viewDoc, setViewDoc] = useState(null);


  async function load() {
    const { data } = await api.get(`/admin/students/${id}/`);
    setData(data);
    setValues(data);
    if (data.end_date) setEndDateInput(data.end_date);
  }

  useEffect(() => {
    let live = true;
    api
      .get(`/admin/students/${id}/`)
      .then((r) => {
        if (live) {
          setData(r.data);
          setValues(r.data);
          if (r.data.end_date) setEndDateInput(r.data.end_date);
        }
      })
      .catch(async (e) => {
        const msg = await errorText(e);
        if (live) setError(msg);
      });
    return () => {
      live = false;
    };
  }, [id]);

  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );

  async function perform(action, success) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await action();
      await load();
      setMessage(success);
    } catch (e) {
      setError(await errorText(e));
    } finally {
      setBusy(false);
      setConfirm(false);
    }
  }

  async function showPreview() {
    if (!data.end_date && !endDateInput) {
      setError("Please set and save the internship End Date before previewing the certificate.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (endDateInput && endDateInput !== data.end_date) {
        await api.patch(`/admin/internships/${data.internship_id}/end-date/`, {
          end_date: endDateInput,
        });
        await load();
      }
      setPreview(
        URL.createObjectURL(
          await pdfBlob(`/admin/certificates/preview/${data.internship_id}/`),
        ),
      );
    } catch (e) {
      setError(await errorText(e));
    } finally {
      setBusy(false);
    }
  }

  function handleStartGenerate() {
    setError("");
    if (!data.end_date && !endDateInput) {
      setError("Please set the internship End Date before generating the certificate.");
      return;
    }
    setConfirm(true);
  }

  if (!data) return error ? <Notice message={error} /> : <Loading />;

  return (
    <>
      <Link to="/admin/students" className="back-link">
        ← All students
      </Link>
      <div className="d-flex justify-content-between align-items-center my-3 gap-3 flex-wrap">
        <div>
          <div className="d-flex align-items-center gap-2 flex-wrap">
            <h1 className="mb-0">{data.full_name}</h1>
            {data.candidate_type === "SCHOOL_STUDENT" && (
              <span className="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle py-1 px-2">
                <i className="bi bi-backpack2 me-1"></i> School Student Intern
              </span>
            )}
            {data.candidate_type === "COLLEGE_COMPLETED" && (
              <span className="badge bg-info-subtle text-info-emphasis border border-info-subtle py-1 px-2">
                <i className="bi bi-briefcase me-1"></i> College Completed Student Intern
              </span>
            )}
            {(!data.candidate_type || data.candidate_type === "COLLEGE_INTERN") && (
              <span className="badge bg-primary-subtle text-primary border border-primary-subtle py-1 px-2">
                <i className="bi bi-mortarboard me-1"></i> College Intern
              </span>
            )}
          </div>
          <p className="text-secondary mb-0 mt-1">
            {data.register_number} · {data.email}
          </p>
        </div>
        <Status value={data.status} />
      </div>

      <Notice message={error} />
      <Notice message={message} type="success" />

      {/* Admin End Date Control Box */}
      {!data.certificate && (
        <section className="card p-3 mb-4 border-primary bg-light shadow-sm">
          <div className="row align-items-center g-3">
            <div className="col-lg-7">
              <h2 className="h6 mb-1 text-primary fw-bold">
                <i className="bi bi-calendar-check me-2"></i>Fix Internship End Date (Admin Control)
              </h2>
              <p className="text-secondary small mb-0">
                Student registered with Start date: <strong>{data.start_date || "Not set"}</strong>.
                {data.end_date ? (
                  <> Fixed End date: <strong className="text-success">{data.end_date}</strong> ({data.duration_days} days)</>
                ) : (
                  <span className="text-danger fw-semibold"> End date is not yet fixed! Admin must set End date before generating certificate.</span>
                )}
              </p>
            </div>
            <div className="col-lg-5">
              <div className="input-group">
                <input
                  type="date"
                  className="form-control"
                  value={endDateInput || ""}
                  min={data.start_date}
                  onChange={(e) => setEndDateInput(e.target.value)}
                />
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={busy || !endDateInput || endDateInput === data.end_date}
                  onClick={() =>
                    perform(async () => {
                      await api.patch(
                        `/admin/internships/${data.internship_id}/end-date/`,
                        { end_date: endDateInput },
                      );
                    }, "End date updated successfully.")
                  }
                >
                  Save End Date
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Action Buttons */}
      <section className="card p-4 mb-4">
        <div className="d-flex flex-wrap gap-2">
          {!data.certificate && (
            <button
              className="btn btn-outline-primary"
              disabled={busy}
              onClick={() => {
                setEditing(!editing);
                setPreview("");
              }}
            >
              {editing ? "Cancel editing" : "Edit student details"}
            </button>
          )}

          {data.status === "REGISTERED" && (
            <button
              className="btn btn-primary"
              disabled={busy || editing}
              onClick={() =>
                perform(
                  () =>
                    api.patch(
                      `/admin/internships/${data.internship_id}/status/`,
                      { status: "IN_PROGRESS" },
                    ),
                  "Internship marked in progress.",
                )
              }
            >
              Mark in progress
            </button>
          )}

          {data.status === "IN_PROGRESS" && (
            <button
              className="btn btn-primary"
              disabled={busy || editing}
              onClick={() =>
                perform(
                  () =>
                    api.patch(
                      `/admin/internships/${data.internship_id}/status/`,
                      { status: "COMPLETED" },
                    ),
                  "Internship marked completed.",
                )
              }
            >
              Mark completed
            </button>
          )}

          {!data.certificate && (
            <>
              <button
                className="btn btn-outline-primary"
                disabled={busy || editing}
                onClick={showPreview}
              >
                {busy ? "Please wait…" : "Preview certificate"}
              </button>
              <button
                className="btn btn-success"
                disabled={busy || editing}
                onClick={handleStartGenerate}
              >
                <i className="bi bi-patch-check me-1"></i> Generate certificate
              </button>
            </>
          )}
        </div>

        {editing ? (
          <form
            className="mt-4"
            onSubmit={(e) => {
              e.preventDefault();
              perform(async () => {
                await api.put(`/admin/students/${id}/`, values);
                setEditing(false);
              }, "Student updated.");
            }}
          >
            <StudentFields
              values={values}
              onChange={(e) =>
                setValues({ ...values, [e.target.name]: e.target.value })
              }
            />
            <button className="btn btn-primary mt-3" disabled={busy}>
              Save corrections
            </button>
          </form>
        ) : (
          <>
            <dl className="details-grid mt-4">
              {[
                ["Category / Role", data.candidate_type_display || "College Intern"],
                [
                  data.candidate_type === "SCHOOL_STUDENT"
                    ? "School Name"
                    : data.candidate_type === "COLLEGE_COMPLETED"
                    ? "Graduated College"
                    : "College Name",
                  data.college_name,
                ],
                [
                  data.candidate_type === "SCHOOL_STUDENT"
                    ? "Board / Stream"
                    : "Department",
                  data.department,
                ],
                [
                  data.candidate_type === "SCHOOL_STUDENT"
                    ? "Class / Standard"
                    : data.candidate_type === "COLLEGE_COMPLETED"
                    ? "Qualification / Degree"
                    : "Course / Degree",
                  data.course,
                ],
                [
                  data.candidate_type === "SCHOOL_STUDENT"
                    ? "School Roll Number"
                    : data.candidate_type === "COLLEGE_COMPLETED"
                    ? "Member / Reg ID"
                    : "Register Number",
                  data.register_number,
                ],
                ["Gender", data.gender],
                ["Mobile", data.mobile_number],
                ["Project", data.project_name],
                ["Start date", data.start_date],
                ["End date", data.end_date || "Not fixed yet (Admin must set)"],
                ["Duration", data.duration_days ? `${data.duration_days} days` : "Pending end date"],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>

            {/* Candidate Verification Documents Section */}
            {(() => {
              const collegeIdUrl = resolveMediaUrl(data.college_id_card);
              const isPdf =
                collegeIdUrl &&
                (collegeIdUrl.toLowerCase().includes(".pdf") ||
                  collegeIdUrl.startsWith("data:application/pdf"));
              const selfieUrl = resolveMediaUrl(data.selfie_photo);
              const docTitle =
                data.candidate_type === "SCHOOL_STUDENT"
                  ? "School ID Card / Student Proof"
                  : data.candidate_type === "COLLEGE_COMPLETED"
                  ? "Any ID Proof"
                  : "College ID Card";

              return (
                <div className="mt-4 pt-3 border-top">
                  <h2 className="h6 fw-bold mb-3 text-secondary text-uppercase tracking-wide">
                    <i className="bi bi-shield-check me-2 text-primary"></i>Candidate Registration Documents
                  </h2>
                  <div className="row g-4">
                    {/* College ID Card */}
                    <div className="col-md-6">
                      <div className="card p-3 h-100 bg-white border shadow-sm">
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <span className="small fw-bold text-uppercase text-secondary">
                            <i className="bi bi-person-badge me-1"></i> {docTitle}
                          </span>
                          {collegeIdUrl && (
                            <span className="badge text-bg-success">
                              <i className="bi bi-check-circle me-1"></i> Attached
                            </span>
                          )}
                        </div>

                        {collegeIdUrl ? (
                          <div>
                            {isPdf ? (
                              <div className="p-4 border rounded bg-light text-center mb-3">
                                <i className="bi bi-file-earmark-pdf-fill text-danger fs-1 d-block mb-2"></i>
                                <span className="fw-semibold text-dark d-block mb-1">
                                  College ID Card (PDF)
                                </span>
                                <small className="text-muted d-block mb-3">
                                  Document is attached in PDF format.
                                </small>
                                <div className="d-flex justify-content-center gap-2">
                                  <button
                                    type="button"
                                    className="btn btn-sm btn-outline-primary"
                                    onClick={() =>
                                      setViewDoc({
                                        title: "College ID Card (PDF)",
                                        url: collegeIdUrl,
                                        isPdf: true,
                                      })
                                    }
                                  >
                                    <i className="bi bi-eye me-1"></i> Preview PDF
                                  </button>
                                  <a
                                    href={collegeIdUrl}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="btn btn-sm btn-primary"
                                  >
                                    <i className="bi bi-box-arrow-up-right me-1"></i> Open in New Tab
                                  </a>
                                </div>
                              </div>
                            ) : (
                              <div>
                                <div
                                  className="border rounded p-1 mb-3 bg-light text-center"
                                  style={{ cursor: "pointer", overflow: "hidden" }}
                                  onClick={() =>
                                    setViewDoc({
                                      title: "College ID Card",
                                      url: collegeIdUrl,
                                      isPdf: false,
                                    })
                                  }
                                  title="Click to view full image"
                                >
                                  <img
                                    src={collegeIdUrl}
                                    alt="College ID Card"
                                    style={{
                                      maxHeight: "180px",
                                      maxWidth: "100%",
                                      objectFit: "contain",
                                      borderRadius: "4px",
                                    }}
                                  />
                                </div>
                                <div className="d-flex gap-2">
                                  <button
                                    type="button"
                                    className="btn btn-sm btn-outline-primary"
                                    onClick={() =>
                                      setViewDoc({
                                        title: "College ID Card",
                                        url: collegeIdUrl,
                                        isPdf: false,
                                      })
                                    }
                                  >
                                    <i className="bi bi-arrows-fullscreen me-1"></i> Enlarge ID
                                  </button>
                                  <a
                                    href={collegeIdUrl}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="btn btn-sm btn-link text-decoration-none"
                                  >
                                    Open Full ID ↗
                                  </a>
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="p-4 text-center text-muted border border-dashed rounded bg-light">
                            <i className="bi bi-file-earmark-x fs-2 d-block mb-1 text-secondary"></i>
                            <small>No College ID card uploaded for this candidate.</small>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Selfie Photo */}
                    <div className="col-md-6">
                      <div className="card p-3 h-100 bg-white border shadow-sm">
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <span className="small fw-bold text-uppercase text-secondary">
                            <i className="bi bi-camera me-1"></i> Candidate Selfie Photo
                          </span>
                          {selfieUrl && (
                            <span className="badge text-bg-success">
                              <i className="bi bi-check-circle me-1"></i> Attached
                            </span>
                          )}
                        </div>

                        {selfieUrl ? (
                          <div className="d-flex align-items-center gap-3">
                            <div
                              style={{ cursor: "pointer" }}
                              onClick={() =>
                                setViewDoc({
                                  title: `${data.full_name} - Selfie Photo`,
                                  url: selfieUrl,
                                  isPdf: false,
                                })
                              }
                              title="Click to enlarge"
                            >
                              <img
                                src={selfieUrl}
                                alt="Candidate Selfie"
                                style={{
                                  width: "110px",
                                  height: "110px",
                                  objectFit: "cover",
                                  borderRadius: "50%",
                                  border: "4px solid #198754",
                                  boxShadow: "0 2px 8px rgba(0,0,0,0.12)",
                                }}
                              />
                            </div>
                            <div>
                              <h3 className="h6 mb-1 text-dark">{data.full_name}</h3>
                              <small className="text-muted d-block mb-3">
                                Selfie captured during candidate registration.
                              </small>
                              <div className="d-flex gap-2">
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-success"
                                  onClick={() =>
                                    setViewDoc({
                                      title: `${data.full_name} - Selfie Photo`,
                                      url: selfieUrl,
                                      isPdf: false,
                                    })
                                  }
                                >
                                  <i className="bi bi-arrows-fullscreen me-1"></i> Enlarge Photo
                                </button>
                                <a
                                  href={selfieUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="btn btn-sm btn-link text-decoration-none"
                                >
                                  Open Full Selfie ↗
                                </a>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="p-4 text-center text-muted border border-dashed rounded bg-light">
                            <i className="bi bi-person-x fs-2 d-block mb-1 text-secondary"></i>
                            <small>No selfie photo uploaded for this candidate.</small>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}

          </>
        )}
      </section>

      {/* Certificate Preview (Watermarked) */}
      {preview && (
        <section className="card p-4 mb-4">
          <h2 className="h4">Certificate preview</h2>
          <p className="text-secondary">
            Review the spelling, dates, title and pronouns. This preview is not
            a valid certificate.
          </p>
          <iframe
            className="pdf-frame"
            src={preview}
            title="Certificate preview"
          />
          <div className="d-flex gap-2 mt-3">
            <button
              className="btn btn-light"
              onClick={() => {
                setEditing(true);
                setPreview("");
              }}
            >
              Edit student details
            </button>
            <button
              className="btn btn-success"
              disabled={busy}
              onClick={handleStartGenerate}
            >
              Generate final certificate
            </button>
          </div>
        </section>
      )}

      {/* Issued Certificate Section */}
      {data.certificate && (
        <section className="card p-4">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h2 className="h4 mb-0">Issued Certificate: {data.certificate.certificate_id}</h2>
            <Status value={data.certificate.status} />
          </div>
          <p className="text-secondary">
            Certificate is active and published. The student can now download and view this certificate.
          </p>
          <CertificateActions cert={data.certificate} />
        </section>
      )}

      {/* Confirmation Modal */}
      {confirm && (
        <Confirm
          title="Approve and Issue Certificate?"
          busy={busy}
          label="Generate final certificate"
          onCancel={() => setConfirm(false)}
          onConfirm={() =>
            perform(async () => {
              if (endDateInput && endDateInput !== data.end_date) {
                await api.patch(
                  `/admin/internships/${data.internship_id}/end-date/`,
                  { end_date: endDateInput },
                );
              }
              await api.post(
                `/admin/certificates/generate/${data.internship_id}/`,
              );
              setPreview("");
            }, "Certificate generated successfully.")
          }
        >
          <p>
            The certificate will be officially issued for candidate <strong>{data.full_name}</strong> from <strong>{data.start_date}</strong> to <strong>{endDateInput || data.end_date}</strong>.
          </p>
          <p className="text-secondary small mb-0">
            Once generated, the student will immediately see the certificate download option in their dashboard, and the QR code will be publicly verifiable.
          </p>
        </Confirm>
      )}

      {/* Document Lightbox Modal */}

      {viewDoc && (
        <div
          className="modal fade show d-block"
          tabIndex="-1"
          style={{ backgroundColor: "rgba(0,0,0,0.75)", zIndex: 1055 }}
          onClick={() => setViewDoc(null)}
        >
          <div
            className="modal-dialog modal-dialog-centered modal-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-content shadow-lg border-0">
              <div className="modal-header py-2 px-3 bg-light">
                <h5 className="modal-title h6 mb-0 fw-bold">{viewDoc.title}</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setViewDoc(null)}
                />
              </div>
              <div
                className="modal-body p-3 text-center bg-dark d-flex justify-content-center align-items-center"
                style={{ minHeight: "350px" }}
              >
                {viewDoc.isPdf ? (
                  <iframe
                    src={viewDoc.url}
                    title={viewDoc.title}
                    style={{ width: "100%", height: "550px", border: "none" }}
                  />
                ) : (
                  <img
                    src={viewDoc.url}
                    alt={viewDoc.title}
                    style={{
                      maxHeight: "75vh",
                      maxWidth: "100%",
                      objectFit: "contain",
                      borderRadius: "6px",
                    }}
                  />
                )}
              </div>
              <div className="modal-footer py-2 px-3 bg-light d-flex justify-content-between">
                <a
                  href={viewDoc.url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-sm btn-outline-primary"
                >
                  <i className="bi bi-box-arrow-up-right me-1"></i> Open Full in New Tab
                </a>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => setViewDoc(null)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

