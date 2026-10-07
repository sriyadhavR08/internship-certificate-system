import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { downloadCertificate, errorText, pdfBlob } from "../services/api";
import { Notice } from "./Common";
export default function CertificateActions({ cert }) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [url, setUrl] = useState(""),
    [message, setMessage] = useState("");
  useEffect(
    () => () => {
      if (url) URL.revokeObjectURL(url);
    },
    [url],
  );
  async function action(view) {
    setBusy(true);
    setError("");
    try {
      if (view)
        setUrl(
          URL.createObjectURL(
            await pdfBlob(`/certificates/${cert.id}/download/`),
          ),
        );
      else {
        await downloadCertificate(cert);
        setMessage("Download started.");
      }
    } catch (e) {
      setError(await errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="d-flex flex-wrap gap-2">
        <button
          className="btn btn-outline-primary"
          disabled={busy || cert.status === "REVOKED"}
          onClick={() => action(true)}
        >
          {busy ? "Please wait…" : "View certificate"}
        </button>
        <button
          className="btn btn-primary"
          disabled={busy || cert.status === "REVOKED"}
          onClick={() => action(false)}
        >
          Download certificate
        </button>
        <Link className="btn btn-light" to={cert.verification_url}>
          Verify certificate
        </Link>
      </div>
      <div className="mt-2">
        <Notice message={error} />
        <Notice message={message} type="success" />
      </div>
      {url && (
        <div className="mt-3">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="btn btn-sm btn-outline-secondary"
            >
              Open in new tab ↗
            </a>
            <button
              className="btn btn-sm btn-link text-danger text-decoration-none"
              onClick={() => setUrl("")}
            >
              Close preview ✕
            </button>
          </div>
          <iframe
            className="pdf-frame w-100"
            style={{ minHeight: "550px", border: "1px solid #dee2e6", borderRadius: "8px" }}
            src={url}
            title="Issued certificate PDF"
          />
        </div>
      )}
    </>
  );
}
