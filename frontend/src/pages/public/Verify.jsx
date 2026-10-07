import { useEffect, useState, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, errorText } from "../../services/api";
import { Loading, Notice, dateLabel } from "../../components/Common";
import Scanner from "../../components/Scanner";

export default function Verify() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [id, setId] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [captcha, setCaptcha] = useState(null);
  const [captchaAnswer, setCaptchaAnswer] = useState("");
  const [captchaLoading, setCaptchaLoading] = useState(false);
  const [otpDigits, setOtpDigits] = useState(["", "", "", "", "", ""]);
  const otpRefs = useRef([]);

  // Load CAPTCHA challenge (6-digit Security OTP)
  async function loadCaptcha() {
    setCaptchaLoading(true);
    setOtpDigits(["", "", "", "", "", ""]);
    setCaptchaAnswer("");
    try {
      const { data } = await api.get("/public/captcha/");
      setCaptcha(data);
    } catch {
      // Fallback 6-digit numeric OTP if network issue
      const randOtp = Math.floor(100000 + Math.random() * 900000).toString();
      setCaptcha({ question: randOtp, otp: randOtp, code: randOtp, token: "local" });
    } finally {
      setCaptchaLoading(false);
    }
  }

  useEffect(() => {
    loadCaptcha();
  }, [token]);

  const handleDigitChange = (index, value) => {
    const clean = value.replace(/\D/g, "");
    const char = clean ? clean.slice(-1) : "";
    const updated = [...otpDigits];
    updated[index] = char;
    setOtpDigits(updated);
    setCaptchaAnswer(updated.join(""));

    if (char && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace") {
      if (!otpDigits[index] && index > 0) {
        otpRefs.current[index - 1]?.focus();
      }
    } else if (e.key === "ArrowLeft" && index > 0) {
      otpRefs.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasteText = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (!pasteText) return;
    const digits = pasteText.split("");
    const updated = ["", "", "", "", "", ""];
    digits.forEach((d, i) => {
      if (i < 6) updated[i] = d;
    });
    setOtpDigits(updated);
    setCaptchaAnswer(updated.join(""));
    const nextFocus = Math.min(digits.length, 5);
    otpRefs.current[nextFocus]?.focus();
  };

  const fillOtp = () => {
    const code = captcha?.otp || captcha?.code || captcha?.question;
    if (!code) return;
    const digits = String(code).replace(/\D/g, "").slice(0, 6).split("");
    const updated = ["", "", "", "", "", ""];
    digits.forEach((d, i) => {
      if (i < 6) updated[i] = d;
    });
    setOtpDigits(updated);
    setCaptchaAnswer(updated.join(""));
    otpRefs.current[5]?.focus();
  };

  async function handleVerify(e) {
    if (e) e.preventDefault();
    const cleanAnswer = otpDigits.join("").trim() || captchaAnswer.trim();
    if (!cleanAnswer || cleanAnswer.length < 6) {
      setError("Please enter the complete 6-digit Security OTP verification code.");
      return;
    }

    setError("");
    setResult(null);
    setLoading(true);

    try {
      let res;
      const params = {
        captcha_token: captcha?.token,
        captcha_answer: cleanAnswer,
      };

      if (token) {
        res = await api.get(`/public/verify/token/${encodeURIComponent(token)}/`, { params });
      } else {
        if (!id.trim()) {
          setError("Please enter a Certificate ID.");
          setLoading(false);
          return;
        }
        res = await api.get(
          `/public/verify/id/${encodeURIComponent(id.trim().toUpperCase())}/`,
          { params },
        );
      }
      setResult(res.data);
    } catch (e) {
      const msg =
        e.response?.status === 404
          ? "Certificate not found. Please check the Certificate ID or scan a valid certificate QR code."
          : e.response?.data?.captcha
          ? e.response.data.captcha
          : await errorText(e);
      setError(msg);
      loadCaptcha(); // Reload fresh OTP on failure
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="verify-page">
      <div className="text-center mb-4">
        <div className="eyebrow">TRUST & AUTHENTICITY</div>
        <h1 className="mt-2">Verify Internship Certificate</h1>
        <p className="text-secondary">
          Official verification portal powered by Wingroo Digital Systems.
        </p>
      </div>

      <section className="card p-4 shadow-sm">
        {/* If QR Code was scanned with token */}
        {token && !result && (
          <div className="alert alert-info d-flex align-items-center mb-4">
            <i className="bi bi-qr-code-scan fs-3 me-3"></i>
            <div>
              <strong>QR Code Scanned Successfully!</strong>
              <div className="small">
                For certificate authenticity and security, enter the 6-digit OTP code below to view verified details.
              </div>
            </div>
          </div>
        )}

        {/* Verification Form */}
        {!result && (
          <form onSubmit={handleVerify}>
            {!token && (
              <div className="mb-3">
                <label className="form-label fw-semibold" htmlFor="certificate-id">
                  Certificate ID
                </label>
                <input
                  id="certificate-id"
                  className="form-control form-control-lg"
                  placeholder="Enter Certificate ID"
                  value={id}
                  onChange={(e) => setId(e.target.value)}
                  required={!token}
                  maxLength={30}
                />
              </div>
            )}

            {/* Security Verification (OTP Code) Box */}
            <div className="p-3 mb-4 rounded-3 border bg-light text-center">
              <div className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom flex-wrap gap-2">
                <span className="fw-bold text-dark d-flex align-items-center">
                  <i className="bi bi-shield-lock-fill text-primary me-2 fs-5"></i>
                  Security Verification OTP
                </span>
                <div className="d-flex gap-2">
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-primary py-1 px-2"
                    onClick={fillOtp}
                    disabled={captchaLoading || !captcha}
                    title="Click to auto-fill the 6-digit OTP code"
                  >
                    <i className="bi bi-input-cursor-text me-1"></i> Auto-fill OTP
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary py-1 px-2"
                    onClick={loadCaptcha}
                    disabled={captchaLoading}
                    title="Generate new OTP code"
                  >
                    <i className="bi bi-arrow-clockwise me-1"></i> Refresh
                  </button>
                </div>
              </div>

              {/* Display Generated Security OTP Badge */}
              <div className="my-3">
                <div className="small text-muted mb-1 text-uppercase fw-semibold" style={{ letterSpacing: "1px" }}>
                  Verification Code
                </div>
                <div className="otp-display-badge">
                  {captchaLoading ? (
                    <span className="fs-6 fw-normal text-light">Generating code…</span>
                  ) : (
                    <span>{captcha?.otp || captcha?.code || captcha?.question || "------"}</span>
                  )}
                </div>
              </div>

              {/* 6-Digit OTP Boxes */}
              <div className="otp-container" onPaste={handlePaste}>
                {otpDigits.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => (otpRefs.current[idx] = el)}
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={1}
                    autoComplete="one-time-code"
                    value={digit}
                    onChange={(e) => handleDigitChange(idx, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, e)}
                    className={`otp-digit-input ${digit ? "filled" : ""}`}
                    aria-label={`OTP Digit ${idx + 1}`}
                    disabled={captchaLoading}
                  />
                ))}
              </div>

              <div className="small text-muted mt-2">
                <i className="bi bi-info-circle me-1"></i>
                Type the 6-digit OTP code above into the boxes to confirm.
              </div>
            </div>

            <button
              className="btn btn-primary btn-lg w-100 shadow-sm"
              disabled={loading || captchaLoading}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" />
                  Verifying certificate…
                </>
              ) : (
                <>
                  <i className="bi bi-patch-check-fill me-2"></i>
                  {token ? "Authenticate & Verify Certificate" : "Verify Certificate"}
                </>
              )}
            </button>
          </form>
        )}

        <div className="mt-3">
          <Notice message={error} />
        </div>

        {/* Certified Verified Result Box */}
        {result && (
          <div className="mt-2">
            <section
              className={`p-4 rounded border text-center ${
                result.status === "VALID"
                  ? "bg-success-subtle border-success"
                  : "bg-danger-subtle border-danger"
              }`}
            >
              <div className="mb-2">
                <i
                  className={`bi bi-${
                    result.status === "VALID"
                      ? "patch-check-fill text-success"
                      : "x-octagon-fill text-danger"
                  }`}
                  style={{ fontSize: "3.5rem" }}
                />
              </div>

              <h2
                className={`h2 fw-bold text-uppercase mb-1 ${
                  result.status === "VALID" ? "text-success" : "text-danger"
                }`}
                style={{ letterSpacing: "1px" }}
              >
                {result.verified_status || (result.status === "VALID" ? "Certified Verified" : "Certificate Revoked")}
              </h2>

              <p className="text-secondary fw-semibold mb-4">
                {result.status === "VALID"
                  ? "This internship credential has been verified as authentic and officially issued by Wingroo."
                  : "This certificate was revoked and is no longer valid."}
              </p>

              {/* Verified Certificate Details Card */}
              <div className="card text-start p-4 bg-white shadow-sm border">
                <div className="d-flex justify-content-between align-items-center border-bottom pb-3 mb-3 flex-wrap gap-2">
                  <div>
                    <span className="text-secondary small text-uppercase fw-bold">Certificate ID</span>
                    <h3 className="h5 text-primary mb-0 fw-bold">{result.certificate_id}</h3>
                  </div>
                  <div className="d-flex align-items-center gap-2">
                    {result.candidate_type_label && (
                      <span className="badge bg-primary-subtle text-primary border border-primary-subtle py-2 px-3">
                        {result.candidate_type_label}
                      </span>
                    )}
                    <span className={`badge ${result.status === "VALID" ? "bg-success" : "bg-danger"} fs-6`}>
                      {result.status}
                    </span>
                  </div>
                </div>

                <dl className="details-grid mb-0">
                  <div>
                    <dt>Candidate Name</dt>
                    <dd className="fw-bold fs-6">{result.student_name}</dd>
                  </div>
                  <div>
                    <dt>Project Title</dt>
                    <dd className="fw-bold">{result.project_name || "—"}</dd>
                  </div>
                  {result.college_name && (
                    <div>
                      <dt>
                        {result.candidate_type === "SCHOOL_STUDENT"
                          ? "School Name"
                          : result.candidate_type === "COLLEGE_COMPLETED"
                          ? "Graduated Institution"
                          : "College / Institution"}
                      </dt>
                      <dd>{result.college_name}</dd>
                    </div>
                  )}
                  {result.department && (
                    <div>
                      <dt>
                        {result.candidate_type === "SCHOOL_STUDENT"
                          ? "Board & Class / Standard"
                          : result.candidate_type === "COLLEGE_COMPLETED"
                          ? "Specialization & Qualification"
                          : "Department & Course"}
                      </dt>
                      <dd>{result.department} {result.course ? `(${result.course})` : ""}</dd>
                    </div>
                  )}
                  <div>
                    <dt>
                      {result.candidate_type === "SCHOOL_STUDENT"
                        ? "Training / Project Period"
                        : "Internship Period"}
                    </dt>
                    <dd>
                      {result.start_date ? dateLabel(result.start_date) : "—"} to{" "}
                      {result.end_date ? dateLabel(result.end_date) : "—"}
                    </dd>
                  </div>
                  <div>
                    <dt>Issue Date</dt>
                    <dd>{result.issue_date ? dateLabel(result.issue_date) : "—"}</dd>
                  </div>
                </dl>

                {result.verified_at && (
                  <div className="mt-3 pt-3 border-top text-secondary small d-flex justify-content-between align-items-center">
                    <span>
                      <i className="bi bi-clock-history me-1"></i> Verified on: {result.verified_at}
                    </span>
                    <span className="text-success fw-semibold">
                      <i className="bi bi-shield-fill-check me-1"></i> Authenticated Record
                    </span>
                  </div>
                )}
              </div>

              <div className="d-flex justify-content-center gap-3 mt-4">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => window.print()}
                >
                  <i className="bi bi-printer me-1"></i> Print Verification Proof
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    setResult(null);
                    setId("");
                    loadCaptcha();
                    if (token) navigate("/verify");
                  }}
                >
                  Verify Another Certificate
                </button>
              </div>
            </section>
          </div>
        )}

        {/* Camera Scanner for Certificates */}
        {!result && (
          <>
            <hr className="my-4" />
            <Scanner />
          </>
        )}
      </section>

      <p className="text-secondary small text-center mt-3">
        <i aria-hidden="true" className="bi bi-shield-lock me-1" />
        Official digital credential system with encrypted verification token. Student personal contact details remain protected.
      </p>
    </div>
  );
}
