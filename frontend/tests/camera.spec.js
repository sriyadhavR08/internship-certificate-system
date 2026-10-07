import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const fixture = process.env.WINGROO_QR_CAMERA;
test.use({
  launchOptions: {
    args: fixture
      ? [
          "--use-fake-device-for-media-stream",
          "--use-fake-ui-for-media-stream",
          `--use-file-for-fake-video-capture=${fixture}`,
        ]
      : [],
  },
});
test("camera decodes the real QR extracted from the generated PDF", async ({
  page,
}) => {
  test.skip(
    !fixture,
    "Set WINGROO_QR_CAMERA to a Y4M fixture created from an issued PDF QR.",
  );
  const result = JSON.parse(
    fs.readFileSync(
      path.resolve(
        process.env.WINGROO_QA_DIR || "../../../work",
        "browser-result.json",
      ),
      "utf8",
    ),
  );
  await page.goto("/verify");
  await page.getByRole("button", { name: "Open camera", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(result.verificationPath));
  await expect(
    page.getByRole("heading", { name: "Certificate Revoked", exact: true }),
  ).toBeVisible();
});
