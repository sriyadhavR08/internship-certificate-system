import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Notice } from "./Common";
import { parseVerificationQR } from "../utils/qr";
export default function Scanner() {
  const scanner = useRef(null),
    mounted = useRef(true);
  const [active, setActive] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const navigate = useNavigate();
  async function stop() {
    const current = scanner.current;
    if (current?.isScanning) await current.stop();
    if (mounted.current) setActive(false);
  }
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      const current = scanner.current;
      if (current?.isScanning) current.stop().catch(() => {});
    };
  }, []);
  async function start() {
    setError("");
    setBusy(true);
    try {
      const { Html5Qrcode } = await import("html5-qrcode");
      const current = new Html5Qrcode("qr-reader");
      scanner.current = current;
      await current.start(
        { facingMode: "environment" },
        { fps: 8, qrbox: { width: 220, height: 220 } },
        async (text) => {
          try {
            const token = parseVerificationQR(text, window.location.origin);
            await stop();
            navigate(`/verify/${token}`);
          } catch {
            setError(
              "This QR code is not a Wingroo certificate verification link.",
            );
          }
        },
        () => {},
      );
      if (!mounted.current) {
        await current.stop();
        return;
      }
      setActive(true);
    } catch {
      if (mounted.current)
        setError(
          "Unable to access camera. Allow camera permission, check that a camera is connected, and use HTTPS or localhost. You can also enter the certificate ID.",
        );
    } finally {
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <section className="scanner-section">
      <h2 className="h5">
        <i aria-hidden="true" className="bi bi-qr-code-scan me-2" />
        Scan a certificate QR
      </h2>
      <p className="text-secondary">
        Point your camera at the QR printed on the certificate.
      </p>
      <Notice message={error} />
      <div id="qr-reader" />
      <button
        type="button"
        className="btn btn-outline-primary mt-2"
        disabled={busy}
        onClick={
          active
            ? () =>
                stop().catch(() =>
                  setError(
                    "Could not stop camera. Close this page to release it.",
                  ),
                )
            : start
        }
      >
        {busy ? "Opening camera…" : active ? "Stop camera" : "Open camera"}
      </button>
    </section>
  );
}
