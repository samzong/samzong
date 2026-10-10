#!/usr/bin/env node

import {spawnSync} from "node:child_process";
import {createRequire} from "node:module";
import {existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync} from "node:fs";
import {homedir, platform} from "node:os";
import {dirname, join} from "node:path";
import {serverArgs} from "./mcp-config.mjs";

const piConfigPath = join(homedir(), ".config/mcp/mcp.json");
const openCodeConfigPath = join(homedir(), ".config/opencode/opencode.json");
const cursorConfigPath = join(homedir(), ".cursor/mcp.json");
const kimiConfigPath = join(process.env.KIMI_CODE_HOME || join(homedir(), ".kimi-code"), "mcp.json");
const dshConfigPath = join(process.env.DSH_HOME || join(homedir(), ".dsh"), "cordis.patch.yml");
const dshEntryId = "mcp-chrome-devtools";
const dshEntry = {
  id: dshEntryId,
  name: "@deepseek-ai/dsh-mcp-client",
  config: {
    serverName: "chrome-devtools",
    transport: "stdio",
    command: "npx",
    args: serverArgs,
  },
};

const clients = {
  codex: {
    inspect: ["codex", "mcp", "get", "chrome-devtools", "--json"],
    install: ["codex", "mcp", "add", "chrome-devtools", "--", "npx", ...serverArgs],
    remove: ["codex", "mcp", "remove", "chrome-devtools"],
    matches(config) {
      return (
        config?.transport?.type === "stdio" &&
        config.transport.command === "npx" &&
        JSON.stringify(config.transport.args) === JSON.stringify(serverArgs)
      );
    },
  },
  claude: {
    inspect: ["claude", "mcp", "get", "chrome-devtools"],
    install: ["claude", "mcp", "add", "--scope", "user", "chrome-devtools", "--", "npx", ...serverArgs],
    remove: ["claude", "mcp", "remove", "chrome-devtools", "--scope", "user"],
    matches(config) {
      return config?.command === "npx" && JSON.stringify(config.args) === JSON.stringify(serverArgs);
    },
    parse(result) {
      const command = result.stdout.match(/^\s*Command:\s*(.+)$/m)?.[1]?.trim();
      const args = result.stdout.match(/^\s*Args:\s*(.*)$/m)?.[1]?.trim().split(/\s+/).filter(Boolean) ?? [];
      return {command, args};
    },
  },
  pi: {
    inspectState: inspectPi,
    mutate: mutatePi,
    preview: {
      install: `Install npm:pi-mcp-adapter and configure ${piConfigPath}`,
      remove: `Remove chrome-devtools from ${piConfigPath} and remove npm:pi-mcp-adapter`,
    },
  },
  opencode: {
    inspectState: inspectOpenCode,
    mutate: mutateOpenCode,
    preview: {
      install: `Configure chrome-devtools in ${openCodeConfigPath}`,
      remove: `Remove chrome-devtools from ${openCodeConfigPath}`,
    },
  },
  grok: {
    inspectState: inspectGrok,
    install: ["grok", "mcp", "add", "--scope", "user", "chrome-devtools", "--", "npx", ...serverArgs],
    remove: ["grok", "mcp", "remove", "--scope", "user", "chrome-devtools"],
  },
  "cursor-agent": {
    inspectState: inspectCursorAgent,
    mutate: mutateCursorAgent,
    preview: {
      install: `Configure and enable chrome-devtools in ${cursorConfigPath}`,
      remove: `Disable and remove chrome-devtools from ${cursorConfigPath}`,
    },
  },
  "kimi-code": {
    inspectState: inspectKimiCode,
    mutate: mutateKimiCode,
    preview: {
      install: `Configure chrome-devtools in ${kimiConfigPath}`,
      remove: `Remove chrome-devtools from ${kimiConfigPath}`,
    },
  },
  "deepseek-harness": {
    inspectState: inspectDeepSeekHarness,
    mutate: mutateDeepSeekHarness,
    preview: {
      install: `Configure chrome-devtools for every DSH profile in ${dshConfigPath}`,
      remove: `Remove chrome-devtools from ${dshConfigPath}`,
    },
  },
};

const rawArgs = process.argv.slice(2);
const json = rawArgs.includes("--json");
const apply = rawArgs.includes("--apply");
const positional = rawArgs.filter((arg) => !["--json", "--apply"].includes(arg));

if (rawArgs.includes("--help")) {
  process.stdout.write("Usage: setup.mjs <install|remove> <client> [--apply] [--json]\n");
  process.exit(0);
}

const [action, clientName, ...extra] = positional;

if (!new Set(["install", "remove"]).has(action) || !clientName || extra.length > 0) {
  process.stderr.write("Usage: setup.mjs <install|remove> <client> [--apply] [--json]\n");
  process.exit(2);
}

const client = clients[clientName];
if (!client) {
  process.stderr.write(`Unsupported client: ${clientName}\n`);
  process.exit(2);
}

function run(command) {
  const [file, ...args] = command;
  const result = spawnSync(file, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    timeout: 30000,
  });
  return {
    status: result.status,
    stdout: result.stdout?.trim() ?? "",
    stderr: result.stderr?.trim() ?? "",
    error: result.error?.code ?? null,
  };
}

function inspect() {
  if (client.inspectState) {
    return client.inspectState();
  }
  const result = run(client.inspect);
  if (result.status !== 0) {
    return {present: false, matches: false, conflict: false};
  }
  try {
    const config = client.parse ? client.parse(result) : JSON.parse(result.stdout);
    const matches = client.matches(config);
    return {present: true, matches, conflict: !matches};
  } catch {
    return {present: true, matches: false, conflict: true};
  }
}

function inspectPi() {
  const packageResult = run(["pi", "list"]);
  const adapterInstalled = packageResult.status === 0 && packageResult.stdout.includes("npm:pi-mcp-adapter");
  let entry = null;

  if (existsSync(piConfigPath)) {
    try {
      entry = JSON.parse(readFileSync(piConfigPath, "utf8"))?.mcpServers?.["chrome-devtools"] ?? null;
    } catch {
      return {present: true, matches: false, conflict: true};
    }
  }

  const entryMatches =
    entry?.command === "npx" && JSON.stringify(entry.args) === JSON.stringify(serverArgs);
  return {
    present: adapterInstalled || Boolean(entry),
    matches: adapterInstalled && entryMatches,
    conflict: Boolean(entry) && !entryMatches,
  };
}

function readPiConfig() {
  if (!existsSync(piConfigPath)) {
    return {};
  }
  return JSON.parse(readFileSync(piConfigPath, "utf8"));
}

function writePiConfig(config) {
  mkdirSync(dirname(piConfigPath), {recursive: true});
  writeFileSync(piConfigPath, `${JSON.stringify(config, null, 2)}\n`, "utf8");
}

function mutatePi(action) {
  try {
    const packageResult = run(["pi", "list"]);
    const adapterInstalled = packageResult.status === 0 && packageResult.stdout.includes("npm:pi-mcp-adapter");
    const config = readPiConfig();
    config.mcpServers ??= {};

    if (action === "install") {
      if (!adapterInstalled) {
        const installResult = run(["pi", "install", "npm:pi-mcp-adapter"]);
        if (installResult.status !== 0) {
          return installResult;
        }
      }
      config.mcpServers["chrome-devtools"] = {command: "npx", args: serverArgs};
      writePiConfig(config);
      return {status: 0, stdout: "", stderr: "", error: null};
    }

    delete config.mcpServers["chrome-devtools"];
    writePiConfig(config);
    if (!adapterInstalled || Object.keys(config.mcpServers).length > 0) {
      return {status: 0, stdout: "", stderr: "", error: null};
    }
    return run(["pi", "remove", "npm:pi-mcp-adapter"]);
  } catch (error) {
    return {status: 1, stdout: "", stderr: error.message, error: error.code ?? null};
  }
}

function inspectOpenCode() {
  if (!existsSync(openCodeConfigPath)) {
    return {present: false, matches: false, conflict: false};
  }
  try {
    const entry = JSON.parse(readFileSync(openCodeConfigPath, "utf8"))?.mcp?.["chrome-devtools"] ?? null;
    const matches =
      entry?.type === "local" &&
      JSON.stringify(entry.command) === JSON.stringify(["npx", ...serverArgs]);
    return {present: Boolean(entry), matches, conflict: Boolean(entry) && !matches};
  } catch {
    return {present: true, matches: false, conflict: true};
  }
}

function mutateOpenCode(action) {
  try {
    const config = existsSync(openCodeConfigPath)
      ? JSON.parse(readFileSync(openCodeConfigPath, "utf8"))
      : {$schema: "https://opencode.ai/config.json"};
    config.mcp ??= {};
    if (action === "install") {
      config.mcp["chrome-devtools"] = {type: "local", command: ["npx", ...serverArgs]};
    } else {
      delete config.mcp["chrome-devtools"];
    }
    mkdirSync(dirname(openCodeConfigPath), {recursive: true});
    writeFileSync(openCodeConfigPath, `${JSON.stringify(config, null, 2)}\n`, "utf8");
    return {status: 0, stdout: "", stderr: "", error: null};
  } catch (error) {
    return {status: 1, stdout: "", stderr: error.message, error: error.code ?? null};
  }
}

function inspectGrok() {
  const result = run(["grok", "mcp", "list"]);
  if (result.status !== 0) {
    return {present: false, matches: false, conflict: false};
  }
  const present = result.stdout.includes("chrome-devtools");
  const matches =
    present &&
    result.stdout.includes("npx") &&
    serverArgs.every((arg) => result.stdout.includes(arg));
  return {present, matches, conflict: present && !matches};
}

function inspectCursorAgent() {
  if (!existsSync(cursorConfigPath)) {
    return {present: false, matches: false, conflict: false};
  }
  try {
    const entry = JSON.parse(readFileSync(cursorConfigPath, "utf8"))?.mcpServers?.["chrome-devtools"] ?? null;
    const configMatches =
      entry?.command === "npx" && JSON.stringify(entry.args) === JSON.stringify(serverArgs);
    const listResult = run(["cursor-agent", "mcp", "list"]);
    const ready = listResult.status === 0 && listResult.stdout.includes("chrome-devtools: ready");
    return {
      present: Boolean(entry),
      matches: configMatches && ready,
      conflict: Boolean(entry) && !configMatches,
    };
  } catch {
    return {present: true, matches: false, conflict: true};
  }
}

function mutateCursorAgent(action) {
  try {
    const config = existsSync(cursorConfigPath)
      ? JSON.parse(readFileSync(cursorConfigPath, "utf8"))
      : {mcpServers: {}};
    config.mcpServers ??= {};
    mkdirSync(dirname(cursorConfigPath), {recursive: true});

    if (action === "install") {
      config.mcpServers["chrome-devtools"] = {command: "npx", args: serverArgs};
      writeFileSync(cursorConfigPath, `${JSON.stringify(config, null, 2)}\n`, "utf8");
      return run(["cursor-agent", "mcp", "enable", "chrome-devtools"]);
    }

    run(["cursor-agent", "mcp", "disable", "chrome-devtools"]);
    delete config.mcpServers["chrome-devtools"];
    writeFileSync(cursorConfigPath, `${JSON.stringify(config, null, 2)}\n`, "utf8");
    return {status: 0, stdout: "", stderr: "", error: null};
  } catch (error) {
    return {status: 1, stdout: "", stderr: error.message, error: error.code ?? null};
  }
}

function readJsonConfig(path) {
  if (!existsSync(path)) {
    return {};
  }
  return JSON.parse(readFileSync(path, "utf8"));
}

function writeJsonConfig(path, config) {
  mkdirSync(dirname(path), {recursive: true});
  writeFileSync(path, `${JSON.stringify(config, null, 2)}\n`, "utf8");
}

function inspectKimiCode() {
  if (!existsSync(kimiConfigPath)) {
    return {present: false, matches: false, conflict: false};
  }
  try {
    const entry = readJsonConfig(kimiConfigPath)?.mcpServers?.["chrome-devtools"] ?? null;
    const matches =
      entry?.command === "npx" && JSON.stringify(entry.args) === JSON.stringify(serverArgs);
    return {present: Boolean(entry), matches, conflict: Boolean(entry) && !matches};
  } catch {
    return {present: true, matches: false, conflict: true};
  }
}

function mutateKimiCode(action) {
  try {
    const config = readJsonConfig(kimiConfigPath);
    config.mcpServers ??= {};
    if (action === "install") {
      config.mcpServers["chrome-devtools"] = {command: "npx", args: serverArgs};
    } else {
      delete config.mcpServers["chrome-devtools"];
    }
    writeJsonConfig(kimiConfigPath, config);
    return {status: 0, stdout: "", stderr: "", error: null};
  } catch (error) {
    return {status: 1, stdout: "", stderr: error.message, error: error.code ?? null};
  }
}

function dshYaml() {
  const locator = platform() === "win32" ? "where" : "which";
  const located = run([locator, "dsh"]);
  if (located.status !== 0 || !located.stdout) {
    throw new Error("dsh executable not found");
  }
  const binary = realpathSync(located.stdout.split(/\r?\n/)[0]);
  const requireFromDsh = createRequire(binary);
  const yaml = requireFromDsh("js-yaml");
  const jsExpression = new yaml.Type("tag:yaml.org,2002:js", {
    kind: "scalar",
    resolve: (value) => typeof value === "string",
    construct: (value) => ({__jsExpr: value}),
  });
  return {yaml, schema: yaml.JSON_SCHEMA.extend(jsExpression)};
}

function readDshPatches() {
  if (!existsSync(dshConfigPath)) {
    return [];
  }
  const {yaml, schema} = dshYaml();
  const patches = yaml.load(readFileSync(dshConfigPath, "utf8"), {schema});
  if (!Array.isArray(patches)) {
    throw new Error(`${dshConfigPath} must contain a top-level YAML array`);
  }
  return patches;
}

function dshEntries(patches) {
  return patches.flatMap((patch) => (Array.isArray(patch?.insert) ? patch.insert : []));
}

function dshEntryMatches(entry) {
  return (
    entry?.id === dshEntryId &&
    entry.name === dshEntry.name &&
    entry.config?.serverName === dshEntry.config.serverName &&
    entry.config?.transport === dshEntry.config.transport &&
    entry.config?.command === dshEntry.config.command &&
    JSON.stringify(entry.config?.args) === JSON.stringify(serverArgs)
  );
}

function inspectDeepSeekHarness() {
  try {
    const entries = dshEntries(readDshPatches());
    const candidates = entries.filter(
      (entry) =>
        entry?.id === dshEntryId ||
        entry?.config?.serverName === "chrome-devtools" ||
        entry?.config?.args?.includes?.("chrome-devtools-mcp@latest"),
    );
    const matches = candidates.length === 1 && dshEntryMatches(candidates[0]);
    return {present: candidates.length > 0, matches, conflict: candidates.length > 0 && !matches};
  } catch {
    return {present: true, matches: false, conflict: true};
  }
}

function renderDshEntry() {
  return [
    "- insert:",
    `    - id: ${dshEntry.id}`,
    `      name: '${dshEntry.name}'`,
    "      config:",
    `        serverName: ${dshEntry.config.serverName}`,
    `        transport: ${dshEntry.config.transport}`,
    `        command: ${dshEntry.config.command}`,
    `        args: ${JSON.stringify(dshEntry.config.args)}`,
    "",
  ].join("\n");
}

function mutateDeepSeekHarness(action) {
  try {
    dshYaml();
    const rendered = renderDshEntry();
    const existing = existsSync(dshConfigPath) ? readFileSync(dshConfigPath, "utf8") : "";
    if (action === "install") {
      const base = existing.trim() === "[]" ? "" : existing.trimEnd();
      mkdirSync(dirname(dshConfigPath), {recursive: true});
      writeFileSync(dshConfigPath, `${base ? `${base}\n` : ""}${rendered}`, "utf8");
    } else {
      if (!existing.includes(rendered)) {
        throw new Error("Refusing to remove a DeepSeek Harness entry not rendered by this setup script");
      }
      const remaining = existing.replace(rendered, "").trim();
      writeFileSync(dshConfigPath, remaining ? `${remaining}\n` : "[]\n", "utf8");
    }
    return {status: 0, stdout: "", stderr: "", error: null};
  } catch (error) {
    return {status: 1, stdout: "", stderr: error.message, error: error.code ?? null};
  }
}

function displayCommand(command) {
  return command.map((arg) => (/^[A-Za-z0-9@._:/=-]+$/.test(arg) ? arg : JSON.stringify(arg))).join(" ");
}

const before = inspect();
let status = "PLANNED";
let detail = "";
const command = action === "install" ? client.install : client.remove;

if (action === "install" && before.present && before.matches) {
  status = "UNCHANGED";
  detail = "Expected chrome-devtools MCP configuration already exists";
} else if (action === "install" && before.conflict) {
  status = "CONFLICT";
  detail = "A different chrome-devtools MCP configuration already exists";
} else if (action === "remove" && !before.present) {
  status = "UNCHANGED";
  detail = "No chrome-devtools MCP configuration exists";
} else if (!apply) {
  detail = client.preview
    ? `Run with --apply to execute: ${client.preview[action]}`
    : `Run with --apply to execute: ${displayCommand(command)}`;
} else {
  const mutation = client.mutate ? client.mutate(action) : run(command);
  if (mutation.status !== 0) {
    status = "FAILED";
    detail = mutation.stderr || mutation.stdout || mutation.error || "Client command failed";
  } else {
    const after = inspect();
    const verified = action === "install" ? after.present && after.matches : !after.present;
    status = verified ? "APPLIED" : "FAILED";
    detail = verified ? "Mutation applied and verified" : "Mutation command succeeded but verification failed";
  }
}

const report = {action, client: clientName, apply, status, detail};

if (json) {
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
} else {
  process.stdout.write(`${status} ${clientName} ${action}: ${detail}\n`);
}

process.exit(new Set(["PLANNED", "UNCHANGED", "APPLIED"]).has(status) ? 0 : 1);
