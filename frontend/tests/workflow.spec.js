import { test, expect } from "@playwright/test";
import { parseVerificationQR } from "../src/utils/qr";
import fs from "node:fs";
import path from "node:path";
const qaDirectory = path.resolve(process.env.WINGROO_QA_DIR || "../../../work");
const credentialFile = path.join(qaDirectory, "browser-credentials.json");
const admin = fs.existsSync(credentialFile)
  ? JSON.parse(fs.readFileSync(credentialFile, "utf8"))
  : null;
const artifactDirectory = path.resolve("../docs/qa");
fs.mkdirSync(artifactDirectory, { recursive: true });

async function login(page, email, password) {
  await page.goto("/login");
  await page.getByLabel("Email", { exact: false }).fill(email);
  await page.getByLabel("Password *", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Login", exact: true }).click();
}

test("QR parser accepts only this portal and valid tokens", () => {
  const token = "A".repeat(43);
  expect(
    parseVerificationQR(
      `http://localhost:5173/verify/${token}`,
      "http://localhost:5173",
    ),
  ).toBe(token);
  for (const value of [
    `https://evil.example/verify/${token}`,
    `javascript:alert(1)`,
    `http://localhost:5173/verify/1`,
    `http://localhost:5173/verify/${token}?redirect=bad`,
    `http://localhost:5173@evil.example/verify/${token}`,
  ])
    expect(() => parseVerificationQR(value, "http://localhost:5173")).toThrow();
});

test("responsive public pages and scanner denial", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "Experience earned. Achievement verified.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("img", { name: "Wingroo", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: path.join(artifactDirectory, "home-desktop.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: path.join(artifactDirectory, "home-mobile.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Toggle navigation" }).click();
  await page.getByRole("link", { name: "Register", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Create your student account" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: path.join(artifactDirectory, "register-mobile.png"),
    fullPage: true,
  });
  await page.goto("/verify");
  await page
    .getByLabel("Certificate ID", { exact: true })
    .fill("INT-0000-00000");
  await page
    .getByRole("button", { name: "Verify certificate", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("Certificate not found");
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      throw new DOMException("Denied", "NotAllowedError");
    };
  });
  await page.reload();
  await page.getByRole("button", { name: "Open camera" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Unable to access camera",
  );
});

test("register → review → preview → issue → download → verify → revoke", async ({
  page,
}) => {
  test.skip(
    !admin,
    "Create a local QA admin and provide work/browser-credentials.json as documented.",
  );
  const stamp = Date.now();
  const email = `kaviya-${stamp}@example.test`;
  const password = `Cedar!Mosaic7River#`;
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/register");
  for (const [label, value] of [
    ["Full name", "Kaviya"],
    ["Email", email],
    ["Mobile number", "9876543210"],
    ["College name", "Wingroo QA College"],
    ["Department", "Computer Science"],
    ["Course / Degree", "BSc Computer Science"],
    ["Register number", `QA${stamp}`],
    ["Project name", "Zentime"],
    ["Start date", "2026-09-01"],
    ["End date", "2026-09-30"],
  ])
    await page.getByLabel(`${label} *`, { exact: true }).fill(value);
  await page.getByLabel("Gender *", { exact: true }).selectOption("FEMALE");
  await page.getByLabel("Password *", { exact: true }).fill(password);
  await page.getByLabel("Confirm password *", { exact: true }).fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByText(
      "Registration successful. Your internship is now registered.",
    ),
  ).toBeVisible();
  await login(page, email, password);
  await expect(page).toHaveURL(/student\/dashboard/);
  await expect(
    page.getByRole("button", { name: "Certificate not yet available" }),
  ).toBeDisabled();
  await page.screenshot({
    path: path.join(artifactDirectory, "student-pending.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/login/);
  await login(page, admin.email, admin.password);
  await expect(page).toHaveURL(/admin\/dashboard/);
  await page.screenshot({
    path: path.join(artifactDirectory, "admin-dashboard.png"),
    fullPage: true,
  });
  await page.getByRole("link", { name: "Students", exact: true }).click();
  await page.getByLabel("Search students").fill(email);
  await page.getByRole("button", { name: "Apply filters" }).click();
  await page.getByRole("link", { name: "View / Review" }).click();
  await page
    .getByRole("button", { name: "Edit student details", exact: true })
    .click();
  await page.getByLabel("Full name *", { exact: true }).fill("Kaviya R");
  await page.getByRole("button", { name: "Save corrections" }).click();
  await expect(
    page.getByText("Student updated.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Mark in progress", exact: true })
    .click();
  await expect(
    page.getByText("Internship marked in progress.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Mark completed", exact: true })
    .click();
  await expect(
    page.getByText("Internship marked completed.", { exact: true }),
  ).toBeVisible();
  const previewResponse = page.waitForResponse(
    (r) => r.url().includes("/certificates/preview/") && r.status() === 200,
  );
  await page
    .getByRole("button", { name: "Preview certificate", exact: true })
    .click();
  fs.writeFileSync(
    path.join(qaDirectory, "preview.pdf"),
    await (await previewResponse).body(),
  );
  await expect(
    page.getByTitle("Certificate preview", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Generate final certificate", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Generate final certificate", exact: true })
    .click();
  await expect(
    page.getByText("Certificate generated successfully.", { exact: true }),
  ).toBeVisible();
  const verificationPath = await page
    .getByRole("link", { name: "Verify certificate", exact: true })
    .last()
    .getAttribute("href");
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/login/);
  await login(page, email, password);
  await expect(
    page.getByText("Congratulations! Your internship certificate is ready."),
  ).toBeVisible();
  await page.screenshot({
    path: path.join(artifactDirectory, "student-issued.png"),
    fullPage: true,
  });
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download certificate", exact: true })
    .click();
  const file = await download;
  await file.saveAs(path.join(qaDirectory, "issued-certificate.pdf"));
  const certificateId = file.suggestedFilename().replace(".pdf", "");
  await page
    .getByRole("link", { name: "Verify certificate", exact: true })
    .last()
    .click();
  await expect(
    page.getByRole("heading", { name: "Certificate Verified", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: path.join(artifactDirectory, "verified-desktop.png"),
    fullPage: true,
  });
  await page.goto("/verify");
  await page.getByLabel("Certificate ID", { exact: true }).fill(certificateId);
  await page
    .getByRole("button", { name: "Verify certificate", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Certificate Verified", exact: true }),
  ).toBeVisible();
  // An expired access token should be refreshed once and the protected page should still load.
  await page.evaluate(() => {
    const tokens = JSON.parse(sessionStorage.getItem("tokens"));
    tokens.access = "expired.invalid.token";
    sessionStorage.setItem("tokens", JSON.stringify(tokens));
  });
  await page.goto("/student/dashboard");
  await expect(
    page.getByText("Congratulations! Your internship certificate is ready."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/login/);
  await login(page, admin.email, admin.password);
  await page.getByRole("link", { name: "Certificates", exact: true }).click();
  await page.getByLabel("Certificate ID", { exact: true }).fill(certificateId);
  await page.getByRole("button", { name: "Filter", exact: true }).click();
  await page.getByRole("button", { name: "Revoke", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Revoke certificate", exact: true })
    .click();
  await expect(
    page.getByText(
      "Certificate revoked. Public verification now shows Revoked.",
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/login/);
  await page.goto(verificationPath);
  await expect(
    page.getByRole("heading", { name: "Certificate Revoked", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Certificate Verified", exact: true }),
  ).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: path.join(artifactDirectory, "revoked-mobile.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  fs.writeFileSync(
    path.join(qaDirectory, "browser-result.json"),
    JSON.stringify({ certificateId, verificationPath, email, errors }),
  );
  expect(errors).toEqual([]);
});
