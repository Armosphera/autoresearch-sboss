#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const contractPath = path.join(repoRoot, "evals/karpathy/invoice-extractor-contract.json");
const contract = JSON.parse(readFileSync(contractPath, "utf8"));
const expectedFields = ["vendor_name", "invoice_date", "total_amount", "currency", "tax_id"];
const secretPatterns = [
  { label: "github token", pattern: /\b(?:github_pat|gh[pousr])_[A-Za-z0-9_]{16,}/gi },
  { label: "openai-style key", pattern: /\bsk-[A-Za-z0-9_-]{16,}/gi },
  { label: "private key block", pattern: /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/gi },
  { label: "bearer token", pattern: /\bbearer\s+[-._~+/=a-z0-9]{16,}/gi },
  { label: "sensitive env assignment", pattern: /\b[A-Z0-9_]*(?:API_KEY|ACCESS_KEY|PRIVATE_KEY|PASSWORD|SECRET|TOKEN)[A-Z0-9_]*\s*[:=]\s*["']?[^\r\n"']+["']?/gi },
];

function numberFromContract(value, fallback, name) {
  const number = Number(value ?? fallback);
  if (!Number.isFinite(number) || number <= 0) {
    throw new Error(`${name} must be a positive finite number`);
  }
  return number;
}

const evalBudgetMinutes = numberFromContract(contract.eval?.timeBudgetMinutes, 5, "timeBudgetMinutes");
const evalTimeoutMinutes = numberFromContract(contract.eval?.timeoutMinutes, 10, "timeoutMinutes");
const evalBudgetSec = Math.ceil(evalBudgetMinutes * 60);
const evalTimeoutMs = Math.ceil(evalTimeoutMinutes * 60_000);

function sanitizedEvalEnv() {
  const env = {};
  for (const key of ["PATH", "HOME", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "LC_CTYPE"]) {
    if (process.env[key]) env[key] = process.env[key];
  }
  return {
    ...env,
    CI: "1",
    PYTHONDONTWRITEBYTECODE: "1",
    PYTHONUNBUFFERED: "1",
    EXPERIMENT_BUDGET_SEC: String(evalBudgetSec),
    EVAL_SET_PATH: path.join(repoRoot, "eval_set.json"),
  };
}

function parseNumber(pattern, text) {
  const match = text.match(pattern);
  return match ? Number(match[1]) : null;
}

function secretLabels(text) {
  const labels = [];
  for (const sentinel of secretPatterns) {
    sentinel.pattern.lastIndex = 0;
    if (sentinel.pattern.test(text)) labels.push(sentinel.label);
  }
  return labels;
}

function redactSecrets(text) {
  let redacted = text;
  for (const sentinel of secretPatterns) {
    sentinel.pattern.lastIndex = 0;
    redacted = redacted.replace(sentinel.pattern, `[REDACTED:${sentinel.label}]`);
  }
  return redacted;
}

const result = spawnSync(process.env.PYTHON || "python3", ["eval.py"], {
  cwd: repoRoot,
  env: sanitizedEvalEnv(),
  encoding: "utf8",
  timeout: evalTimeoutMs,
  maxBuffer: 1024 * 1024,
});

const output = [result.stdout, result.stderr].filter(Boolean).join("\n");
const leakedSecretLabels = secretLabels(output);
if (result.stdout) process.stdout.write(redactSecrets(result.stdout));
if (result.stderr) process.stderr.write(redactSecrets(result.stderr));

const score = parseNumber(/\bscore:\s*([0-9]+(?:\.[0-9]+)?)/, output);
const nItems = parseNumber(/\bn_items:\s*([0-9]+)/, output);
const evalErrors = parseNumber(/\berrors:\s*([0-9]+)/, output);
const errors = [];

if (result.error) {
  errors.push(`eval process error: ${result.error.message}`);
}
if (result.status !== 0) {
  errors.push(`eval exited with status ${result.status}`);
}
if (!Number.isFinite(score)) {
  errors.push("eval output must include a finite score");
} else if (score < 100) {
  errors.push(`score must stay at 100.0000, got ${score}`);
}
if (nItems !== 20) {
  errors.push(`eval must run the 20-item root invoice set, got ${nItems ?? "missing"}`);
}
if (evalErrors !== 0) {
  errors.push(`eval errors must remain zero, got ${evalErrors ?? "missing"}`);
}

for (const field of expectedFields) {
  const fieldScore = parseNumber(new RegExp(`\\b${field}=([0-9]+(?:\\.[0-9]+)?)`), output);
  if (fieldScore !== 100) {
    errors.push(`${field} score must be 100.0, got ${fieldScore ?? "missing"}`);
  }
}

if (leakedSecretLabels.length) {
  errors.push(`eval output contains key-shaped secrets: ${leakedSecretLabels.join(", ")}`);
}

console.log(`score=${Number.isFinite(score) ? score.toFixed(4) : "0.0000"}`);
console.log(`failing_checks=${errors.length}`);
if (errors.length) {
  console.error(`invoice_extractor_contract_error=${errors[0]}`);
}
process.exitCode = errors.length ? 1 : 0;
