#!/usr/bin/env node

import { spawn } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "..");
const API_DIR = path.join(REPO_ROOT, "apps", "api");
const OPENAPI_JSON = path.join(REPO_ROOT, "packages", "api-client", "openapi.json");
const TYPES_DIR = path.join(REPO_ROOT, "packages", "api-client", "src", "gen");
const TYPES_FILE = path.join(TYPES_DIR, "v1.d.ts");
const JS_YAML_SHIM = path.join(REPO_ROOT, "scripts", "js-yaml-types-shim.cjs");
const OPENAPI_OUTPUT_ARG = "../../packages/api-client/openapi.json";

function log(message) {
  console.log(`[generate-api-types] ${message}`);
}

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: "inherit",
      ...options,
    });

    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) {
        reject(
          new Error(`Command \"${command} ${args.join(" ")}\" exited with code ${code}`),
        );
        return;
      }

      resolve();
    });
  });
}

async function normalizeJson(filePath) {
  const raw = await readFile(filePath, "utf8");
  const parsed = JSON.parse(raw);
  await writeFile(filePath, `${JSON.stringify(parsed, null, 2)}\n`, "utf8");
}

async function normalizeLineEndings(filePath) {
  const raw = await readFile(filePath, "utf8");
  let normalized = raw.replace(/\r\n/g, "\n");
  if (!normalized.endsWith("\n")) {
    normalized = `${normalized}\n`;
  }
  await writeFile(filePath, normalized, "utf8");
}

async function main() {
  log("Preparing directories");
  await mkdir(path.dirname(OPENAPI_JSON), { recursive: true });
  await mkdir(TYPES_DIR, { recursive: true });

  log("Exporting OpenAPI schema (Django)");
  await run(
    "uv",
    ["run", "python", "manage.py", "export_openapi_schema", "--output", OPENAPI_OUTPUT_ARG],
    { cwd: API_DIR },
  );
  await normalizeJson(OPENAPI_JSON);

  log("Generating TypeScript definitions (openapi-typescript)");
  const shimOption = `--require ${JS_YAML_SHIM}`;
  const nodeOptions = process.env.NODE_OPTIONS
    ? `${process.env.NODE_OPTIONS} ${shimOption}`
    : shimOption;
  await run(
    "npx",
    ["openapi-typescript", "packages/api-client/openapi.json", "-o", "packages/api-client/src/gen/v1.d.ts"],
    { cwd: REPO_ROOT, env: { ...process.env, NODE_OPTIONS: nodeOptions } },
  );
  await normalizeLineEndings(TYPES_FILE);

  log("Done");
}

main().catch((error) => {
  console.error(`[generate-api-types] ${error.message}`);
  process.exitCode = 1;
});
