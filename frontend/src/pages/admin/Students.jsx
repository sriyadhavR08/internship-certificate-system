import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, errorText } from "../../services/api";
import {
  Loading,
  Notice,
  Status,
  Pagination,
  dateLabel,
} from "../../components/Common";
export default function Students() {
  const [filters, setFilters] = useState({}),
    [query, setQuery] = useState({}),
    [page, setPage] = useState(1),
    [data, setData] = useState(null),
    [error, setError] = useState("");
  const location = useLocation();
  useEffect(() => {
    let live = true;
    setData(null);
    setError("");
    api
      .get("/admin/students/", { params: { ...query, page } })
      .then((r) => {
        if (live) setData(r.data);
      })
      .catch(async (e) => {
        const message = await errorText(e);
        if (live) setError(message);
      });
    return () => {
      live = false;
    };
  }, [query, page]);
  return (
    <>
      <div className="eyebrow">MANAGEMENT</div>
      <h1 className="mt-2">
        {location.pathname.endsWith("internships") ? "Internships" : "Students"}
      </h1>
      <p className="text-secondary">
        Review details and guide each internship through approval.
      </p>
      <section className="card p-4">
        <form
          className="row g-3 mb-4"
          onSubmit={(e) => {
            e.preventDefault();
            setPage(1);
            setQuery({ ...filters });
          }}
        >
          <div className="col-lg-4">
            <label className="form-label" htmlFor="search">
              Search students
            </label>
            <input
              id="search"
              className="form-control"
              placeholder="Name, register number or email"
              value={filters.search || ""}
              onChange={(e) =>
                setFilters({ ...filters, search: e.target.value })
              }
            />
          </div>
          <div className="col-lg-4">
            <label className="form-label" htmlFor="project">
              Project
            </label>
            <input
              id="project"
              className="form-control"
              placeholder="Exact project name"
              value={filters.project_name || ""}
              onChange={(e) =>
                setFilters({ ...filters, project_name: e.target.value })
              }
            />
          </div>
          <div className="col-lg-4">
            <label className="form-label" htmlFor="status">
              Status
            </label>
            <select
              id="status"
              className="form-select"
              value={filters.status || ""}
              onChange={(e) =>
                setFilters({ ...filters, status: e.target.value })
              }
            >
              <option value="">All statuses</option>
              {[
                "REGISTERED",
                "IN_PROGRESS",
                "COMPLETED",
                "CERTIFICATE_ISSUED",
              ].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
          {["start_date", "end_date"].map((key) => (
            <div className="col-md-4" key={key}>
              <label className="form-label" htmlFor={key}>
                {key.replace("_", " ")}
              </label>
              <input
                id={key}
                type="date"
                className="form-control"
                value={filters[key] || ""}
                onChange={(e) =>
                  setFilters({ ...filters, [key]: e.target.value })
                }
              />
            </div>
          ))}
          <div className="col-md-4 d-flex align-items-end gap-2">
            <button className="btn btn-primary">Apply filters</button>
            <button
              type="button"
              className="btn btn-light"
              onClick={() => {
                setFilters({});
                setQuery({});
                setPage(1);
              }}
            >
              Clear
            </button>
          </div>
        </form>
        <Notice message={error} />
        {!data && !error ? (
          <Loading />
        ) : (
          data && (
            <>
              <div className="table-responsive">
                <table className="table align-middle">
                  <thead>
                    <tr>
                      {[
                        "Candidate / Category",
                        "Institution / College",
                        "Project",
                        "Dates",
                        "Internship",
                        "Certificate",
                        "Actions",
                      ].map((h) => (
                        <th key={h}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.results.map((s) => (
                      <tr key={s.id}>
                        <td>
                          <div className="d-flex align-items-center gap-2 mb-1 flex-wrap">
                            <strong>{s.full_name}</strong>
                            {s.candidate_type === "SCHOOL_STUDENT" && (
                              <span className="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle py-1 px-2" style={{ fontSize: "0.72rem" }}>
                                <i className="bi bi-backpack2 me-1"></i> School Intern
                              </span>
                            )}
                            {s.candidate_type === "COLLEGE_COMPLETED" && (
                              <span className="badge bg-info-subtle text-info-emphasis border border-info-subtle py-1 px-2" style={{ fontSize: "0.72rem" }}>
                                <i className="bi bi-briefcase me-1"></i> Completed Intern
                              </span>
                            )}
                            {(!s.candidate_type || s.candidate_type === "COLLEGE_INTERN") && (
                              <span className="badge bg-primary-subtle text-primary border border-primary-subtle py-1 px-2" style={{ fontSize: "0.72rem" }}>
                                <i className="bi bi-mortarboard me-1"></i> College Intern
                              </span>
                            )}
                          </div>
                          <small className="d-block text-secondary">
                            {s.register_number}
                          </small>
                        </td>
                        <td>{s.college_name}</td>
                        <td>{s.project_name}</td>
                        <td className="text-nowrap">
                          {dateLabel(s.start_date)}
                          <small className="d-block">
                            to {dateLabel(s.end_date)}
                          </small>
                        </td>
                        <td>
                          <Status value={s.status} />
                        </td>
                        <td>
                          <Status value={s.certificate?.status} />
                        </td>
                        <td>
                          <Link
                            className="btn btn-sm btn-outline-primary text-nowrap"
                            to={`/admin/students/${s.id}`}
                          >
                            View / Review
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!data.results.length && (
                  <p className="text-center py-4 text-secondary">
                    No students match these filters.
                  </p>
                )}
              </div>
              <Pagination page={page} count={data.count} onChange={setPage} />
            </>
          )
        )}
      </section>
    </>
  );
}
