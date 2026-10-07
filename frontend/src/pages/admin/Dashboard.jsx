import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "../../services/api";
import { Loading, Notice, Status } from "../../components/Common";
export default function AdminDashboard() {
  const [data, setData] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    api
      .get("/admin/dashboard/")
      .then((r) => setData(r.data))
      .catch(async (e) => setError(await errorText(e)));
  }, []);
  if (error) return <Notice message={error} />;
  if (!data) return <Loading />;
  return (
    <>
      <div className="eyebrow">OVERVIEW</div>
      <h1 className="mt-2">Admin dashboard</h1>
      <p className="text-secondary">
        Review internships. Recognize achievement.
      </p>
      <div className="row g-3 my-4">
        {Object.entries(data.counts).map(([label, count], i) => (
          <div className="col-sm-6 col-xl-3" key={label}>
            <section className="card stat-card">
              <i
                className={`bi bi-${["people", "briefcase", "check-circle", "patch-check"][i]}`}
              />
              <strong>{count}</strong>
              <span>{label}</span>
            </section>
          </div>
        ))}
      </div>
      <section className="card p-4 mb-4">
        <div className="d-flex justify-content-between mb-3">
          <h2 className="h5">Recent students</h2>
          <Link to="/admin/students">View all</Link>
        </div>
        {data.recent_students.length ? (
          data.recent_students.map((s) => (
            <div className="activity-row" key={s.id}>
              <div>
                <Link to={`/admin/students/${s.id}`}>{s.full_name}</Link>
                <small>
                  {s.project_name} · {s.college_name}
                </small>
              </div>
              <Status value={s.status} />
            </div>
          ))
        ) : (
          <p className="text-secondary">New registrations will appear here.</p>
        )}
      </section>
      <section className="card p-4">
        <h2 className="h5 mb-3">Recent certificates</h2>
        {data.recent_certificates.length ? (
          data.recent_certificates.map((c) => (
            <div className="activity-row" key={c.id}>
              <div>
                <Link to={c.verification_url}>{c.certificate_id}</Link>
                <small>{c.student_name}</small>
              </div>
              <Status value={c.status} />
            </div>
          ))
        ) : (
          <p className="text-secondary">No certificates issued yet.</p>
        )}
      </section>
    </>
  );
}
