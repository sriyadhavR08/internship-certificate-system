import { useState } from "react";
export function Loading() {
  return (
    <div className="py-5 text-center" role="status">
      <span className="spinner-border spinner-border-sm me-2" />
      Loading…
    </div>
  );
}
export function Notice({ message, type = "danger" }) {
  return message ? (
    <div
      role={type === "danger" ? "alert" : "status"}
      className={`alert alert-${type}`}
    >
      {message}
    </div>
  ) : null;
}
export function Status({ value }) {
  const color =
    {
      REGISTERED: "secondary",
      IN_PROGRESS: "primary",
      COMPLETED: "success",
      CERTIFICATE_ISSUED: "success",
      VALID: "success",
      REVOKED: "danger",
    }[value] || "secondary";
  return (
    <span className={`badge text-bg-${color}`}>
      {value?.replaceAll("_", " ") || "Not issued"}
    </span>
  );
}
export function Field({
  name,
  label,
  type = "text",
  value,
  onChange,
  options,
  required = true,
  maxLength,
  ...rest
}) {
  const [visible, setVisible] = useState(false);
  const id = `field-${name}`;
  return (
    <div className="col-md-6">
      <label className="form-label" htmlFor={id}>
        {label}
        {required && " *"}
      </label>
      <div className="input-group">
        {options ? (
          <select
            {...rest}
            id={id}
            className="form-select"
            name={name}
            value={value || ""}
            onChange={onChange}
            required={required}
          >
            <option value="">Select…</option>
            {options.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        ) : (
          <input
            {...rest}
            id={id}
            className="form-control"
            name={name}
            type={type === "password" && visible ? "text" : type}
            value={value || ""}
            onChange={onChange}
            required={required}
            maxLength={maxLength}
          />
        )}
        {type === "password" && (
          <button
            type="button"
            className="btn btn-outline-secondary"
            aria-label={visible ? "Hide password" : "Show password"}
            onClick={() => setVisible(!visible)}
          >
            <i
              aria-hidden="true"
              className={`bi bi-eye${visible ? "-slash" : ""}`}
            />
          </button>
        )}
      </div>
    </div>
  );
}
export function Pagination({ page, count, onChange }) {
  return (
    <div className="d-flex justify-content-between align-items-center mt-3">
      <small className="text-secondary">
        {count} records · Page {page}
      </small>
      <div className="btn-group">
        <button
          className="btn btn-outline-secondary btn-sm"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Previous
        </button>
        <button
          className="btn btn-outline-secondary btn-sm"
          disabled={page * 20 >= count}
          onClick={() => onChange(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
export function Confirm({
  title,
  children,
  onConfirm,
  onCancel,
  busy,
  label = "Confirm",
  danger = false,
}) {
  return (
    <div className="dialog-backdrop">
      <section
        className="card dialog-card"
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <h2 className="h4">{title}</h2>
        <div className="my-3">{children}</div>
        <div className="d-flex gap-2 justify-content-end">
          <button className="btn btn-light" disabled={busy} onClick={onCancel}>
            Cancel
          </button>
          <button
            className={`btn btn-${danger ? "danger" : "primary"}`}
            disabled={busy}
            onClick={onConfirm}
          >
            {busy ? "Please wait…" : label}
          </button>
        </div>
      </section>
    </div>
  );
}
export function dateLabel(value) {
  return value
    ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString("en-GB")
    : "—";
}
