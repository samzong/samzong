#!/usr/bin/env node

import {spawn} from "node:child_process";
import {serverArgs, serverCommand} from "./mcp-config.mjs";

const initializeTimeoutMs = 30000;
const toolTimeoutMs = 30000;

class JsonRpcClient {
  constructor(command, args) {
    this.buffer = "";
    this.nextId = 1;
    this.pending = new Map();
    this.exited = false;
    this.child = spawn(command, args, {stdio: ["pipe", "pipe", "pipe"]});
    this.child.stdout.on("data", (chunk) => this.read(chunk));
    this.child.stdin.on("error", (error) => this.fail(error));
    this.child.on("error", (error) => this.fail(error));
    this.child.on("exit", (code, signal) => {
      this.exited = true;
      if (this.pending.size > 0) {
        this.fail(new Error(`MCP server exited before responding: code=${code} signal=${signal}`));
      }
    });
  }

  read(chunk) {
    this.buffer += chunk.toString();
    for (;;) {
      const newline = this.buffer.indexOf("\n");
      if (newline < 0) {
        return;
      }
      const line = this.buffer.slice(0, newline).trim();
      this.buffer = this.buffer.slice(newline + 1);
      if (!line) {
        continue;
      }
      let message;
      try {
        message = JSON.parse(line);
      } catch {
        this.fail(new Error("MCP server emitted invalid JSON-RPC"));
        return;
      }
      const request = this.pending.get(message.id);
      if (!request) {
        continue;
      }
      clearTimeout(request.timer);
      this.pending.delete(message.id);
      if (message.error) {
        request.reject(new Error(message.error.message || "MCP request failed"));
      } else {
        request.resolve(message.result);
      }
    }
  }

  fail(error) {
    for (const request of this.pending.values()) {
      clearTimeout(request.timer);
      request.reject(error);
    }
    this.pending.clear();
  }

  send(message) {
    this.child.stdin.write(`${JSON.stringify(message)}\n`);
  }

  request(method, params, timeoutMs) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`${method} timed out after ${timeoutMs}ms`));
      }, timeoutMs);
      this.pending.set(id, {resolve, reject, timer});
      this.send({jsonrpc: "2.0", id, method, params});
    });
  }

  notify(method, params = {}) {
    this.send({jsonrpc: "2.0", method, params});
  }

  async close() {
    if (this.exited) {
      return;
    }
    const exited = new Promise((resolve) => this.child.once("exit", resolve));
    this.child.stdin.end();
    const closed = await Promise.race([
      exited.then(() => true),
      new Promise((resolve) => setTimeout(() => resolve(false), 2000)),
    ]);
    if (!closed && !this.exited) {
      this.child.kill("SIGTERM");
      await Promise.race([
        exited,
        new Promise((resolve) => setTimeout(resolve, 2000)),
      ]);
    }
  }
}

function textOf(result) {
  return (result?.content ?? [])
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("\n");
}

function pageIds(result) {
  return new Set([...textOf(result).matchAll(/^(\d+):/gm)].map((match) => Number(match[1])));
}

function selectedPageId(result) {
  return [...textOf(result).matchAll(/^(\d+):.*\[selected\]$/gm)]
    .map((match) => Number(match[1]))
    .at(-1);
}

function assertToolResult(result, tool) {
  if (result?.isError) {
    const detail = textOf(result).replace(/\s+/g, " ").slice(0, 300);
    throw new Error(`${tool} failed${detail ? `: ${detail}` : ""}`);
  }
}

async function callTool(client, name, args) {
  const result = await client.request(
    "tools/call",
    {name, arguments: args},
    toolTimeoutMs,
  );
  assertToolResult(result, name);
  return result;
}

export async function runLiveCheck(command = serverCommand) {
  const client = new JsonRpcClient(command, serverArgs);
  const checks = [];
  let failure = null;
  let pageId;
  let pageCreated = false;
  let beforePageIds = new Set();

  try {
    const initialized = await client.request(
      "initialize",
      {
        protocolVersion: "2025-06-18",
        capabilities: {},
        clientInfo: {name: "browser-cdp-doctor", version: "1.0.0"},
      },
      initializeTimeoutMs,
    );
    client.notify("notifications/initialized");
    checks.push({
      id: "mcp.initialize",
      status: "PASS",
      detail: `${initialized.serverInfo?.name ?? "unknown"} ${initialized.serverInfo?.version ?? "unknown"}`,
    });

    const listedTools = await client.request("tools/list", {}, toolTimeoutMs);
    const requiredTools = [
      "list_pages",
      "new_page",
      "evaluate_script",
      "take_snapshot",
      "click",
      "close_page",
    ];
    const advertisedTools = listedTools.tools ?? [];
    const missingTools = requiredTools.filter(
      (name) => !advertisedTools.some((tool) => tool.name === name),
    );
    if (missingTools.length > 0) {
      throw new Error(`Missing required tools: ${missingTools.join(", ")}`);
    }
    checks.push({
      id: "mcp.tools",
      status: "PASS",
      detail: `${requiredTools.length} required, ${advertisedTools.length} advertised`,
    });

    const before = await callTool(client, "list_pages", {});
    beforePageIds = pageIds(before);
    const created = await callTool(client, "new_page", {
      url: "about:blank",
      background: true,
    });
    pageCreated = true;
    pageId = selectedPageId(created);
    if (pageId === undefined || beforePageIds.has(pageId)) {
      const after = await callTool(client, "list_pages", {});
      pageId = [...pageIds(after)].find((candidate) => !beforePageIds.has(candidate));
    }
    if (pageId === undefined) {
      throw new Error("Task-owned page was not observed after new_page");
    }
    checks.push({
      id: "chrome.auto_connect",
      status: "PASS",
      detail: "Connected to active Chrome and created a background task-owned page",
    });

    const markerBefore = "CDP_LIVE_CHECK_BEFORE_91F6";
    const markerAfter = "CDP_LIVE_CHECK_AFTER_91F6";
    const setup = await callTool(client, "evaluate_script", {
      pageId,
      function: `() => { document.title = "browser-cdp-live-check"; document.body.innerHTML = '<button id="probe">${markerBefore}</button>'; document.querySelector("#probe").addEventListener("click", event => { event.currentTarget.textContent = "${markerAfter}"; }); return document.querySelector("#probe").textContent; }`,
    });
    if (!textOf(setup).includes(markerBefore)) {
      throw new Error("Runtime write/read sentinel mismatch");
    }

    const snapshot = await callTool(client, "take_snapshot", {pageId});
    const uid = textOf(snapshot).match(
      new RegExp(`uid=([^\\s]+) button "${markerBefore}"`),
    )?.[1];
    if (!uid) {
      throw new Error("Snapshot did not expose the task-owned button");
    }

    await callTool(client, "click", {pageId, uid});
    const verified = await callTool(client, "evaluate_script", {
      pageId,
      function: "() => document.querySelector('#probe')?.textContent",
    });
    if (!textOf(verified).includes(markerAfter)) {
      throw new Error("Input event did not update the task-owned DOM");
    }
    checks.push({
      id: "page.lifecycle",
      status: "PASS",
      detail: "Runtime, snapshot, and input checks passed",
    });
  } catch (error) {
    failure = error;
  } finally {
    if (pageCreated && pageId === undefined) {
      try {
        const current = await callTool(client, "list_pages", {});
        const candidates = [...pageIds(current)].filter(
          (candidate) => !beforePageIds.has(candidate),
        );
        if (candidates.length === 1) {
          pageId = candidates[0];
        } else if (candidates.length === 0) {
          checks.push({
            id: "page.cleanup",
            status: "PASS",
            detail: "No task-owned page remained",
          });
        } else {
          throw new Error("Could not identify the task-owned page without risking unrelated pages");
        }
      } catch (error) {
        checks.push({id: "page.cleanup", status: "FAIL", detail: error.message});
        failure ??= error;
      }
    }
    if (pageId !== undefined) {
      try {
        await callTool(client, "close_page", {pageId});
        const remaining = await callTool(client, "list_pages", {});
        if (pageIds(remaining).has(pageId)) {
          throw new Error("Task-owned page remained open after close_page");
        }
        checks.push({
          id: "page.cleanup",
          status: "PASS",
          detail: "Task-owned page closed",
        });
      } catch (error) {
        checks.push({id: "page.cleanup", status: "FAIL", detail: error.message});
        failure ??= error;
      }
    }
    await client.close();
  }

  if (failure) {
    checks.push({
      id: "mcp.live",
      status: "FAIL",
      detail: failure.message.replace(/\s+/g, " ").slice(0, 300),
    });
    return {status: "FAIL", detail: "Live MCP browser check failed", checks};
  }
  return {status: "PASS", detail: "Live MCP browser check passed", checks};
}
