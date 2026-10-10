#!/usr/bin/env node

import {execFileSync} from "node:child_process";
import {existsSync, readFileSync} from "node:fs";
import {homedir, platform} from "node:os";
import {join} from "node:path";
import {runLiveCheck} from "./live-check.mjs";

const args = process.argv.slice(2);
const clientIndex = args.indexOf("--client");
const selectedClient = clientIndex >= 0 ? args[clientIndex + 1] : null;
const consumedArgs = new Set(["--help", "--json", "--live"]);

if (clientIndex >= 0) {
  consumedArgs.add("--client");
  consumedArgs.add(selectedClient);
}

const unknownArgs = args.filter((arg) => !consumedArgs.has(arg));

if (clientIndex >= 0 && (!selectedClient || selectedClient.startsWith("--"))) {
  process.stderr.write("--client requires a client name\n");
  process.exit(2);
}

if (unknownArgs.length > 0) {
  process.stderr.write(`Unknown argument: ${unknownArgs.join(", ")}\n`);
  process.exit(2);
}

if (args.includes("--help")) {
  process.stdout.write("Usage: doctor.mjs [--client <name>] [--live] [--json]\n");
  process.exit(0);
}

const home = homedir();
const cwd = process.cwd();

function run(command, commandArgs = []) {
  try {
    return {
      ok: true,
      stdout: execFileSync(command, commandArgs, {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"],
        timeout: 3000,
      }).trim(),
    };
  } catch {
    return {ok: false, stdout: ""};
  }
}

function executable(names) {
  const locator = platform() === "win32" ? "where" : "which";
  for (const name of names) {
    const result = run(locator, [name]);
    if (result.ok && result.stdout) {
      return result.stdout.split("\n")[0];
    }
  }
  return null;
}

function inspectFiles(paths, pattern) {
  const matches = [];
  for (const path of paths.filter((candidate) => existsSync(candidate))) {
    try {
      if (pattern.test(readFileSync(path, "utf8"))) {
        matches.push(path);
      }
    } catch {
      continue;
    }
  }
  return matches;
}

function displayPath(path) {
  return path.startsWith(home) ? `~${path.slice(home.length)}` : path;
}

function chromeVersion() {
  if (platform() === "darwin") {
    const result = run("mdls", [
      "-name",
      "kMDItemVersion",
      "-raw",
      "/Applications/Google Chrome.app",
    ]);
    if (result.ok && /^\d+\./.test(result.stdout)) {
      return result.stdout;
    }
  }

  const browser = executable([
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
  ]);
  if (!browser) {
    return null;
  }
  const result = run(browser, ["--version"]);
  const match = result.stdout.match(/\d+(?:\.\d+){1,3}/);
  return match ? match[0] : null;
}

function chromeRunning() {
  if (platform() === "win32") {
    return run("tasklist", ["/FI", "IMAGENAME eq chrome.exe"]).stdout.includes("chrome.exe");
  }
  const exactName = platform() === "darwin" ? "Google Chrome" : "chrome";
  return run("pgrep", ["-x", exactName]).ok;
}

function remoteDebuggingEvidence() {
  const candidates = [];
  if (platform() === "darwin") {
    candidates.push(join(home, "Library/Application Support/Google/Chrome/DevToolsActivePort"));
  } else if (platform() === "linux") {
    candidates.push(
      join(home, ".config/google-chrome/DevToolsActivePort"),
      join(home, ".config/chromium/DevToolsActivePort"),
    );
  } else if (platform() === "win32" && process.env.LOCALAPPDATA) {
    candidates.push(join(process.env.LOCALAPPDATA, "Google/Chrome/User Data/DevToolsActivePort"));
  }

  for (const path of candidates) {
    if (!existsSync(path)) {
      continue;
    }
    try {
      const [port, browserPath] = readFileSync(path, "utf8")
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
      if (!/^\d+$/.test(port) || !browserPath?.startsWith("/devtools/browser/")) {
        continue;
      }
      if (platform() === "win32") {
        return {present: true, listening: null};
      }
      const listener = run("lsof", ["-nP", `-iTCP:${port}`, "-sTCP:LISTEN"]);
      return {present: true, listening: listener.ok && listener.stdout.split("\n").length > 1};
    } catch {
      return {present: false, listening: false};
    }
  }
  return {present: false, listening: false};
}

function nodeSupported(version) {
  const [major = 0, minor = 0] = version
    .replace(/^v/, "")
    .split(".")
    .map((part) => Number.parseInt(part, 10));
  return (major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major >= 23;
}

const clients = [
  {
    id: "codex",
    executables: ["codex"],
    files: [join(home, ".codex/config.toml"), join(cwd, ".codex/config.toml")],
  },
  {
    id: "claude",
    executables: ["claude"],
    files: [join(home, ".claude.json"), join(home, ".claude/settings.json"), join(cwd, ".mcp.json")],
  },
  {
    id: "opencode",
    executables: ["opencode"],
    files: [
      join(home, ".config/opencode/opencode.json"),
      join(home, ".config/opencode/opencode.jsonc"),
      join(cwd, "opencode.json"),
      join(cwd, "opencode.jsonc"),
    ],
  },
  {
    id: "grok",
    executables: ["grok"],
    files: [join(home, ".grok/config.toml"), join(cwd, ".grok/config.toml")],
  },
  {
    id: "cursor-agent",
    executables: ["cursor-agent", "cursor"],
    files: [join(home, ".cursor/mcp.json"), join(cwd, ".cursor/mcp.json")],
  },
  {
    id: "pi",
    executables: ["pi"],
    files: [
      join(home, ".pi/agent/settings.json"),
      join(home, ".config/mcp/mcp.json"),
      join(home, ".pi/agent/mcp.json"),
      join(cwd, ".mcp.json"),
    ],
    adapterPattern: /pi-mcp-adapter/i,
    adapterName: "pi-mcp-adapter",
  },
  {
    id: "kimi-code",
    executables: ["kimi"],
    files: [
      join(process.env.KIMI_CODE_HOME || join(home, ".kimi-code"), "mcp.json"),
      join(cwd, ".mcp.json"),
      join(cwd, ".kimi-code/mcp.json"),
    ],
  },
  {
    id: "deepseek-harness",
    executables: ["dsh"],
    files: [
      join(process.env.DSH_HOME || join(home, ".dsh"), "cordis.patch.yml"),
      join(process.env.DSH_HOME || join(home, ".dsh"), "profiles/web/cordis.patch.yml"),
      join(process.env.DSH_HOME || join(home, ".dsh"), "profiles/headless/cordis.patch.yml"),
      join(process.env.DSH_HOME || join(home, ".dsh"), "profiles/dsh-tui/cordis.patch.yml"),
    ],
    adapterPattern: /@deepseek-ai\/dsh-mcp-client/i,
    adapterName: "@deepseek-ai/dsh-mcp-client",
  },
];

if (selectedClient && !clients.some((client) => client.id === selectedClient)) {
  process.stderr.write(`Unsupported client: ${selectedClient}\n`);
  process.exit(2);
}

const hostChecks = [];
const version = chromeVersion();
const versionMajor = Number.parseInt(version?.split(".")[0] ?? "0", 10);

hostChecks.push({
  id: "chrome.version",
  status: versionMajor >= 144 ? "PASS" : "FAIL",
  detail: version ? `Chrome ${version}` : "Google Chrome not found",
});

const running = chromeRunning();
hostChecks.push({
  id: "chrome.running",
  status: running ? "PASS" : "FAIL",
  detail: running ? "Chrome is running" : "Chrome is not running",
});

const remoteDebugging = remoteDebuggingEvidence();
hostChecks.push({
  id: "chrome.remote_debugging",
  status: remoteDebugging.present && remoteDebugging.listening !== false ? "PASS" : "WARN",
  detail: remoteDebugging.present
    ? remoteDebugging.listening === false
      ? "DevToolsActivePort exists but no listener was verified"
      : "DevToolsActivePort evidence is present"
    : "Remote Debugging is not observable; verify chrome://inspect/#remote-debugging",
});

const node = executable(["node"]);
const nodeVersionResult = node ? run(node, ["--version"]) : {ok: false, stdout: ""};
hostChecks.push({
  id: "runtime.node",
  status: nodeVersionResult.ok && nodeSupported(nodeVersionResult.stdout) ? "PASS" : "FAIL",
  detail: nodeVersionResult.ok ? `Node ${nodeVersionResult.stdout}` : "Node not found",
});

const npx = executable(["npx"]);
hostChecks.push({
  id: "runtime.npx",
  status: npx ? "PASS" : "FAIL",
  detail: npx ? `npx found at ${displayPath(npx)}` : "npx not found",
});

const chromePattern = /chrome[-_ ]devtools|chrome-devtools-mcp/i;
const autoConnectPattern = /--auto(?:connect|-connect)/i;
const usageStatisticsOptOutPattern = /--no-usage-statistics/i;
const performanceCruxOptOutPattern = /--no-performance-crux/i;
const clientChecks = [];

for (const client of clients.filter((candidate) => !selectedClient || candidate.id === selectedClient)) {
  const binary = executable(client.executables);
  if (!binary) {
    clientChecks.push({
      id: `config.${client.id}`,
      status: "SKIP",
      detail: `${client.id} is not installed`,
    });
    continue;
  }

  const configuredFiles = inspectFiles(client.files, chromePattern);
  const canonicalFiles = configuredFiles.filter((path) => {
    try {
      const content = readFileSync(path, "utf8");
      return (
        autoConnectPattern.test(content) &&
        usageStatisticsOptOutPattern.test(content) &&
        performanceCruxOptOutPattern.test(content)
      );
    } catch {
      return false;
    }
  });
  const adapterFiles = client.adapterPattern
    ? inspectFiles(client.files, client.adapterPattern)
    : configuredFiles;

  let status = "PASS";
  let detail = canonicalFiles.length
    ? `Configured in ${canonicalFiles.map(displayPath).join(", ")}`
    : "No chrome-devtools MCP entry found in known config files";

  if (configuredFiles.length === 0 || canonicalFiles.length === 0) {
    status = "FAIL";
    if (configuredFiles.length > 0) {
      detail = `Configured without the canonical auto-connect and privacy flags in ${configuredFiles.map(displayPath).join(", ")}`;
    }
  }

  if (client.adapterPattern && adapterFiles.length === 0) {
    status = "FAIL";
    detail = `${client.adapterName} not found in known config files`;
  }

  clientChecks.push({id: `config.${client.id}`, status, detail});
}

const hostFailure = hostChecks.some((check) => check.status === "FAIL");
const hostWarning = hostChecks.some((check) => check.status === "WARN");
const configFailure = clientChecks.some((check) => check.status === "FAIL");
const liveCheck = args.includes("--live")
  ? await runLiveCheck(npx || undefined)
  : {status: "NOT_RUN", detail: "Run with --live to check the active Chrome session", checks: []};
const liveFailure = liveCheck.status === "FAIL";
const hostVerdict = hostFailure ? "INCOMPLETE" : hostWarning ? "UNKNOWN" : "READY";
const configurationVerdict = configFailure ? "INCOMPLETE" : "READY";
const verdict = hostFailure || configFailure || liveFailure ? "INCOMPLETE" : hostWarning ? "UNKNOWN" : "READY";
const report = {
  verdict,
  hostVerdict,
  configurationVerdict,
  selectedClient,
  liveHandshake: liveCheck.status.toLowerCase(),
  liveCheck,
  hostChecks,
  clientChecks,
};

if (args.includes("--json")) {
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
} else {
  process.stdout.write("browser-cdp doctor\n\n");
  process.stdout.write("Host\n");
  for (const check of hostChecks) {
    process.stdout.write(`${check.status.padEnd(4)} ${check.id.padEnd(28)} ${check.detail}\n`);
  }
  process.stdout.write("\nClient configuration\n");
  for (const check of clientChecks) {
    process.stdout.write(`${check.status.padEnd(4)} ${check.id.padEnd(28)} ${check.detail}\n`);
  }
  if (args.includes("--live")) {
    process.stdout.write("\nLive MCP\n");
    for (const check of liveCheck.checks) {
      process.stdout.write(`${check.status.padEnd(4)} ${check.id.padEnd(28)} ${check.detail}\n`);
    }
  }
  process.stdout.write(`\nHost: ${hostVerdict}\n`);
  process.stdout.write(`Configuration: ${configurationVerdict}\n`);
  process.stdout.write(`Verdict: ${verdict}\n`);
  const liveSummary = liveCheck.status === "NOT_RUN" ? "NOT_RUN (use --live)" : liveCheck.status;
  process.stdout.write(`Live MCP handshake: ${liveSummary}\n`);
}

process.exit(verdict === "READY" ? 0 : 1);
