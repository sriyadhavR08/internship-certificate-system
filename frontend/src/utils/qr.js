export function parseVerificationQR(text, origin) {
  const url = new URL(text);
  const match = url.pathname.match(/^\/verify\/([A-Za-z0-9_-]{43})\/?$/);
  if (
    url.origin !== origin ||
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    !match
  )
    throw new Error("Invalid verification URL");
  return match[1];
}
