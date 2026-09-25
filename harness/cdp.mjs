#!/usr/bin/env node
// Zero-dependency CDP driver for the throwaway Chrome started by run.sh (Node >= 22: global WebSocket).
//
//   node harness/cdp.mjs wait                      wait for DevTools, print version + browser PID
//   node harness/cdp.mjs load <dir>                load (or reload) an unpacked theme/extension, print its id
//   node harness/cdp.mjs uninstall <id>
//   node harness/cdp.mjs layout <layout.json>      build tabs + groups through the helper extension
//   node harness/cdp.mjs eval '<expr>'             run a chrome.* expression in the helper's service worker
//   node harness/cdp.mjs shot <out.png> [--when-front] [--delay <s>]   capture the test window
//   node harness/cdp.mjs close
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const UDD = process.env.VT_UDD;
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

function fail(msg) {
  console.error(`cdp: ${msg}`);
  process.exit(1);
}

if (!UDD) fail("set VT_UDD");
if (UDD.includes("/Library/Application Support/Google/Chrome")) fail("refusing the real Chrome profile");

async function endpoint(timeoutMs = 30000) {
  const file = `${UDD}/DevToolsActivePort`;
  for (const t0 = Date.now(); Date.now() - t0 < timeoutMs; await delay(250)) {
    if (!existsSync(file)) continue;
    const [port, path] = readFileSync(file, "utf8").trim().split("\n");
    if (port && path) return `ws://127.0.0.1:${port}${path}`;
  }
  fail("DevToolsActivePort never appeared (is the test Chrome running?)");
}

class CDP {
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((res, rej) => {
      ws.onopen = res;
      ws.onerror = () => rej(new Error(`cannot connect to ${url}`));
    });
    return new CDP(ws);
  }

  constructor(ws) {
    this.ws = ws;
    this.seq = 0;
    this.pending = new Map();
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      const p = this.pending.get(msg.id);
      if (!p) return;
      this.pending.delete(msg.id);
      if (msg.error) p.rej(new Error(`${msg.error.message}${msg.error.data ? `: ${msg.error.data}` : ""}`));
      else p.res(msg.result);
    };
  }

  send(method, params = {}, sessionId, timeoutMs = 30000) {
    const id = ++this.seq;
    this.ws.send(JSON.stringify({ id, method, params, ...(sessionId && { sessionId }) }));
    return new Promise((res, rej) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        rej(new Error(`${method} timed out`));
      }, timeoutMs);
      this.pending.set(id, { res: (v) => (clearTimeout(timer), res(v)), rej: (e) => (clearTimeout(timer), rej(e)) });
    });
  }

  close() {
    this.ws.close();
  }
}

async function browserPid(cdp) {
  const { processInfo } = await cdp.send("SystemInfo.getProcessInfo");
  return processInfo.find((p) => p.type === "browser")?.id;
}

async function helperSession(cdp) {
  const { id } = await cdp.send("Extensions.loadUnpacked", { path: resolve(HERE, "helper-ext") });
  for (let i = 0; i < 60; i++, await delay(250)) {
    const { targetInfos } = await cdp.send("Target.getTargets");
    const sw = targetInfos.find((t) => t.type === "service_worker" && t.url.startsWith(`chrome-extension://${id}/`));
    if (!sw) continue;
    // After a reload the old worker can linger for a moment; wait for the one that defines buildLayout.
    const attached = await cdp.send("Target.attachToTarget", { targetId: sw.targetId, flatten: true }, undefined, 3000).catch(() => null);
    if (!attached) continue;
    const { sessionId } = attached;
    const probe = await cdp.send("Runtime.evaluate", { expression: "typeof buildLayout", returnByValue: true }, sessionId, 3000).catch(() => null);
    if (probe?.result?.value === "function") return sessionId;
    await cdp.send("Target.detachFromTarget", { sessionId }).catch(() => {});
  }
  fail("helper service worker did not start");
}

async function evaluate(cdp, sessionId, expression) {
  const r = await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }, sessionId, 120000);
  if (r.exceptionDetails) fail(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
  return r.result.value;
}

function osa(...args) {
  return execFileSync("osascript", ["-l", "JavaScript", resolve(ROOT, "tools/winid.js"), ...args], { encoding: "utf8" }).trim();
}

async function shot(cdp, out, { whenFront = false, delaySec = 0 } = {}) {
  const pid = await browserPid(cdp);
  if (whenFront) {
    console.error("waiting for the test window to be frontmost (click it)...");
    while (Number(osa("front")) !== pid) await delay(300);
    await delay(400);
  }
  if (delaySec) await delay(delaySec * 1000);
  const wins = JSON.parse(osa(String(pid)));
  if (!wins.length) fail(`no on-screen window for PID ${pid}`);
  execFileSync("screencapture", ["-x", "-o", "-l", String(wins[0].id), resolve(out)]);
  if (!existsSync(out) || statSync(out).size === 0) fail("screencapture produced nothing (Screen Recording permission?)");
  return { out: resolve(out), window: wins[0] };
}

const [cmd, ...args] = process.argv.slice(2);
const cdp = await CDP.connect(await endpoint());
try {
  switch (cmd) {
    case "wait": {
      const v = await cdp.send("Browser.getVersion");
      console.log(JSON.stringify({ product: v.product, pid: await browserPid(cdp) }));
      break;
    }
    case "load": {
      const { id } = await cdp.send("Extensions.loadUnpacked", { path: resolve(args[0]) });
      console.log(id);
      break;
    }
    case "uninstall":
      await cdp.send("Extensions.uninstall", { id: args[0] });
      break;
    case "layout": {
      const spec = JSON.parse(readFileSync(args[0], "utf8"));
      const session = await helperSession(cdp);
      console.log(JSON.stringify(await evaluate(cdp, session, `buildLayout(${JSON.stringify(spec)})`)));
      break;
    }
    case "eval": {
      const session = await helperSession(cdp);
      console.log(JSON.stringify(await evaluate(cdp, session, args.join(" ")), null, 2));
      break;
    }
    case "shot": {
      const i = args.indexOf("--delay");
      const res = await shot(cdp, args[0], { whenFront: args.includes("--when-front"), delaySec: i >= 0 ? Number(args[i + 1]) : 0 });
      console.log(JSON.stringify(res));
      break;
    }
    case "close":
      await cdp.send("Browser.close").catch(() => {});
      break;
    default:
      fail(`unknown command ${cmd ?? "(none)"}`);
  }
} finally {
  cdp.close();
}
