import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, downloadCertificate, errorText } from "../../services/api";
import {
  Loading,
  Notice,
  Status,
  Confirm,
  Pagination,
  dateLabel,
} from "../../components/Common";
export default function Certificates() {
  const [data, setData] = useState(null),
    [page, setPage] = useState(1),
    [query, setQuery] = useState({}),
    [search, setSearch] = useState(""),
    [status, setStatus] = useState(""),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [confirm, setConfirm] = useState(null),
    [busy, setBusy] = useState(false),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    let live = true;
    setData(null);
    api
      .get("/admin/certificates/", { params: { ...query, page } })
      .then((r) => {
        if (live) setData(r.data);
      })
      .catch(async (e) => {
        const msg = await errorText(e);
        if (live) setError(msg);
      });
    return () => {
      live = false;
    };
  }, [page, query, revision]);
  async function revoke() {
    setBusy(true);
    setError("");
    try {
      await api.patch(`/admin/certificates/${confirm.id}/revoke/`);
      setMessage("Certificate revoked. Public verification now shows Revoked.");
      setConfirm(null);
      setRevision(revision + 1);
    } catch (e) {
      setError(await errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function download(c) {
    setBusy(true);
    try {
      await downloadCertificate(c);
      setMessage("Download started.");
    } catch (e) {
      setError(await errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="eyebrow">ISSUED RECORDS</div>
      <h1 className="mt-2">Certificates</h1>
      <p className="text-secondary">
        Access issued certificates and manage their validity.
      </p>
      <Notice message={error} />
      <Notice message={message} type="success" />
      <section className="card p-4">
        <form
          className="row g-2 mb-4"
          onSubmit={(e) => {
            e.preventDefault();
            setPage(1);
            setQuery({ search, status });
          }}
        >
          <div className="col-md-6">
            <label className="form-label" htmlFor="cert-search">
              Certificate ID
            </label>
            <input
              id="cert-search"
              className="form-control"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="col-md-4">
            <label className="form-label" htmlFor="cert-status">
              Status
            </label>
            <select
              id="cert-status"
              className="form-select"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All statuses</option>
              <option>VALID</option>
              <option>REVOKED</option>
            </select>
          </div>
          <div className="col-md-2 d-flex align-items-end">
            <button className="btn btn-primary">Filter</button>
          </div>
        </form>
        {!data ? (
          <Loading />
        ) : (
          <>
            <div className="table-responsive">
              <table className="table align-middle">
                <thead>
                  <tr>
                    <th>Certificate</th>
                    <th>Student / Project</th>
                    <th>Issued</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((c) => (
                    <tr key={c.id}>
                      <td>{c.certificate_id}</td>
                      <td>
                        {c.student_name}
                        <small className="d-block text-secondary">
                          {c.project_name}
                        </small>
                      </td>
                      <td>{dateLabel(c.issue_date)}</td>
                      <td>
                        <Status value={c.status} />
                      </td>
                      <td>
                        <div className="d-flex gap-2">
                          <Link
                            className="btn btn-sm btn-light"
                            to={c.verification_url}
                          >
                            Verify
                          </Link>
                          <button
                            className="btn btn-sm btn-outline-primary"
                            disabled={busy || c.status === "REVOKED"}
                            onClick={() => download(c)}
                          >
                            Download
                          </button>
                          {c.status === "VALID" && (
                            <button
                              className="btn btn-sm btn-outline-danger"
                              disabled={busy}
                              onClick={() => setConfirm(c)}
                            >
                              Revoke
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!data.results.length && (
                <p className="text-center py-4 text-secondary">
                  No certificates found.
                </p>
              )}
            </div>
            <Pagination page={page} count={data.count} onChange={setPage} />
          </>
        )}
      </section>
      {confirm && (
        <Confirm
          danger
          title="Revoke this certificate?"
          busy={busy}
          label="Revoke certificate"
          onConfirm={revoke}
          onCancel={() => setConfirm(null)}
        >
          <p>
            {confirm.certificate_id} will immediately show as revoked in public
            verification. This action cannot be undone in the portal.
          </p>
        </Confirm>
      )}
    </>
  );
}
