import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/Auth";
import { api, errorText } from "../../services/api";
import { Field, Notice } from "../../components/Common";
import StudentFields from "../../components/StudentFields";
import logo from "../../assets/WINGROO.jpeg";
export function Login() {
  const [values, setValues] = useState({}),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const u = await login(values);
      navigate(u.role === "ADMIN" ? "/admin/dashboard" : "/student/dashboard");
    } catch (e) {
      setError(await errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="card auth-card">
      <img className="auth-logo" src={logo} alt="Wingroo" />
      <h1 className="h3">Welcome back</h1>
      <p className="text-secondary">
        Sign in to access your internship certificate portal.
      </p>
      <Notice message={error} />
      <form onSubmit={submit}>
        <div className="row g-3 single-fields">
          <Field
            name="email"
            label="Email"
            type="email"
            autoComplete="username"
            value={values.email}
            onChange={(e) => setValues({ ...values, email: e.target.value })}
          />
          <Field
            name="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            value={values.password}
            onChange={(e) => setValues({ ...values, password: e.target.value })}
          />
        </div>
        <button className="btn btn-primary w-100 mt-4" disabled={busy}>
          {busy ? "Signing in…" : "Login"}
        </button>
      </form>
      <p className="mb-0 mt-4 text-center">
        New to Wingroo? <Link to="/register">Create an account</Link>
      </p>
    </section>
  );
}
export function Register() {
  const [values, setValues] = useState({ candidate_type: "COLLEGE_INTERN" }),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [done, setDone] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (values.password !== values.confirm_password) {
      setError("Passwords do not match.");
      return;
    }
    const candType = values.candidate_type || "COLLEGE_INTERN";
    if (!values.college_id_card) {
      const docLabel =
        candType === "SCHOOL_STUDENT"
          ? "School ID card / Student ID proof"
          : candType === "COLLEGE_COMPLETED"
          ? "ID proof (Aadhaar / College ID / Degree Certificate / Govt ID)"
          : "College ID card photo";
      setError(`Please attach your ${docLabel}.`);
      return;
    }
    if (!values.selfie_photo) {
      setError("Please provide a selfie photo (Upload file or Snap Photo).");
      return;
    }
    setBusy(true);
    try {
      await api.post("/auth/register/", {
        ...values,
        candidate_type: candType,
      });
      setDone(true);
      window.scrollTo(0, 0);
    } catch (e) {
      setError(await errorText(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="registration">
      <div className="eyebrow">PORTAL ENROLLMENT & REGISTRATION</div>
      <h1 className="mt-2">Create Your Candidate Account</h1>
      <p className="text-secondary">
        Register as a School Student Intern, College Intern, or College Completed Student Intern for your verified credential.
      </p>
      {done ? (
        <section className="card p-5">
          <Notice
            type="success"
            message="Registration successful! Your profile has been registered in the system."
          />
          <Link className="btn btn-primary" to="/login">
            Continue to login
          </Link>
        </section>
      ) : (
        <form className="card registration-form" onSubmit={submit}>
          <StudentFields
            values={values}
            onChange={(e) =>
              setValues({ ...values, [e.target.name]: e.target.value })
            }
            account
          />
          <Notice message={error} />
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-3">
            <span>
              Already registered? <Link to="/login">Login</Link>
            </span>
            <button className="btn btn-primary" disabled={busy}>
              {busy ? "Creating account…" : "Create account"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
