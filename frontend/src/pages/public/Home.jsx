import { Link } from "react-router-dom";
export default function Home() {
  return (
    <>
      <section className="hero row align-items-center g-5">
        <div className="col-lg-7">
          <div className="eyebrow mb-3">YOUR WORK. YOUR ACHIEVEMENT.</div>
          <h1>
            Experience earned.
            <br />
            <span>Achievement verified.</span>
          </h1>
          <p className="lead mt-4">Digital Internship Certificate Portal</p>
          <p className="text-secondary hero-copy">
            Register your internship, access your digital certificate after
            completion and securely verify certificates using QR technology.
          </p>
          <div className="d-flex flex-wrap gap-3 mt-4">
            <Link to="/register" className="btn btn-primary btn-lg">
              Register now{" "}
              <i aria-hidden="true" className="bi bi-arrow-right ms-2" />
            </Link>
            <Link to="/verify" className="btn btn-outline-primary btn-lg">
              Verify certificate
            </Link>
          </div>
        </div>
        <div className="col-lg-5">
          <div className="hero-panel">
            <div className="hero-icon">
              <i aria-hidden="true" className="bi bi-patch-check" />
            </div>
            <div className="eyebrow">WINGROO INTERNSHIPS</div>
            <h2 className="h3 mt-3">A milestone worth keeping.</h2>
            <p className="text-secondary">
              Your internship journey, from registration to a certificate you
              can share with confidence.
            </p>
            <div className="journey-step">
              <span>01</span>
              <div>
                <strong>Register your internship</strong>
                <small>One account. All your details.</small>
              </div>
            </div>
            <div className="journey-step">
              <span>02</span>
              <div>
                <strong>Complete & get approved</strong>
                <small>Reviewed by the Wingroo team.</small>
              </div>
            </div>
            <div className="journey-step">
              <span>03</span>
              <div>
                <strong>Download & verify</strong>
                <small>A secure PDF with QR verification.</small>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="trust-row row g-4">
        <div className="col-md-4">
          <i aria-hidden="true" className="bi bi-person-check" />
          <h3>Reviewed by people</h3>
          <p>
            Certificates are issued only after completion and admin approval.
          </p>
        </div>
        <div className="col-md-4">
          <i aria-hidden="true" className="bi bi-file-earmark-pdf" />
          <h3>Ready when you are</h3>
          <p>Access your approved certificate from your student dashboard.</p>
        </div>
        <div className="col-md-4">
          <i aria-hidden="true" className="bi bi-qr-code-scan" />
          <h3>Easy to verify</h3>
          <p>Scan the QR or enter a certificate ID. No account needed.</p>
        </div>
      </section>
    </>
  );
}
