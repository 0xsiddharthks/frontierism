// Exercise live-model changes without opening a window or touching terminals.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function environment() {
  const texts = [];
  const element = new Proxy({}, {
    get(_target, key) {
      if (key === "when") return (condition, callback) => condition ? callback(element) : element;
      if (key === "child") return (child) => { if (typeof child === "string") texts.push(child); return element; };
      return () => element;
    },
  });
  const values = new Map();
  const stored = new Map();
  return {
    texts,
    api: {
      View: class {}, div: () => element, svg: () => element,
      image: () => element, h_flex: () => element, v_flex: () => element,
      theme: () => ({ chrome: "#111111", dim: "#888888", foreground: "#eeeeee" }),
      openOverlay() {}, closeOverlay() {}, props: () => ({}), window: () => ({ buttons: false }),
      shared: (key) => values.get(key), setShared: (key, value) => values.set(key, value),
      localStorage: { getItem: (key) => stored.get(key), setItem: (key, value) => stored.set(key, value) },
    },
  };
}

function load(name, api) {
  const source = readFileSync(new URL(`./mods/${name}/main.js`, import.meta.url), "utf8")
    .replace(/^import .*;\n/gm, "").replace("export default class", "return class");
  return new Function(...Object.keys(api), source)(...Object.values(api));
}

{
  const { api } = environment();
  const tree = JSON.parse(readFileSync(new URL("./layouts/frontierism.json", import.meta.url)));
  const find = (node, id) => node.id === id ? node : (node.children ?? []).map(c => find(c, id)).find(Boolean);
  const strip = find(tree, "tabs");
  const space = { id: "fixture-space", active: true, tabs: [] };
  const commands = [];
  Object.assign(api, {
    layout: () => tree, spaces: () => [space], panes: () => [],
    run: (command, args) => {
      commands.push([command, args]);
      if (args.id === "tabs") strip.hidden = command === "layout.hide";
    },
  });
  const Tabs = load("frontier-tabs", api);
  const view = new Tabs();
  view.init();
  space.tabs = [{ id: "tab-one", name: "One", active: true }];
  view.render();
  assert.equal(strip.hidden, true, "one tab hides the strip");
  view.render();
  assert.equal(commands.length, 1, "an unchanged model does not keep writing layout state");
  space.tabs.push({ id: "tab-two", name: "Two" });
  view.render();
  assert.equal(strip.hidden, false, "a second tab restores a hidden strip");
  space.tabs = [];
  view.render();
  assert.equal(strip.hidden, true, "an empty tab strip adds no blank toolbar; the workbench keeps the controls");
}

{
  const { api, texts } = environment();
  const statuses = ["idle", "working", "done", "blocked"];
  const agents = statuses.map((status, index) => ({
    address: `fixture-${index}`, pane: `pane-${index}`, tab: `tab-${index}`,
    space: "fixture-space", space_name: "Fixture", title: `✳ Task ${index}`,
    program: { name: "Fixture Agent", agent: true }, status, seq: index, focused: false,
  }));
  let order;
  Object.assign(api, {
    agents: () => agents, terminals: () => [], panes: () => [], focused: () => null,
    spaces: () => [{ tabs: agents.map(a => ({ id: a.tab, name: "Fixture Agent" })) }],
    setAgentOrder: (addresses) => { order = addresses; }, run() {},
  });
  const Agents = load("frontier-agents", api);
  const view = new Agents();
  view.init({}, { timer: { every() {} } });
  view.render();
  assert.deepEqual(order, ["fixture-3", "fixture-2", "fixture-1", "fixture-0"], "attention precedes done, working and idle");
  for (let index = 0; index < 4; index++) assert.ok(texts.includes(`Task ${index}`), "terminal title is cleaned");
  assert.equal(texts.filter(text => text === "Fixture Agent · Fixture").length, 4, "each row identifies its agent and space");
  for (const symbol of ["!", "~", "✓", "○"]) assert.ok(texts.includes(symbol), "each status has its own symbol");
}

{
  const { api, texts } = environment();
  const tree = JSON.parse(readFileSync(new URL("./layouts/frontierism.json", import.meta.url)));
  const find = (node, id) => node.id === id ? node : (node.children ?? []).map(c => find(c, id)).find(Boolean);
  const panel = find(tree, "panel"), body = find(tree, "panel-body");
  find(tree, "tabs").hidden = true;
  let active = { id: "space-one", name: "Project one", active: true };
  let focus = { pane: "fixture-pane", cwd: "/workspace/one", terminal: "fixture-terminal" };
  const pane = { pane: "fixture-pane", title: "✳ Task", cwd: "/workspace/one", branch: "feature", program: { name: "Fixture Agent" } };
  const executions = [], notices = [];
  let editorFails = false;
  let receive;
  Object.assign(api, {
    layout: () => tree, spaces: () => [active], focused: () => focus, panes: () => [pane],
    home: () => "/home/fixture", nextCommand: () => new Promise(resolve => { receive = resolve; }),
    exec: async (...args) => {
      executions.push(args);
      if (editorFails) throw new Error("editor unavailable");
      return { code: 0 };
    },
    notify: (notice) => notices.push(notice),
    run: (command, args) => {
      if (command === "layout.select") body.active = args.child;
      else if (args.id === "panel") panel.hidden = command === "layout.hide";
    },
  });
  const Workbench = load("frontier-workbench", api);
  const view = new Workbench();
  view.init({}, { spawn: task => task({ notify() {} }) });
  const send = async command => { receive(command); await new Promise(resolve => setImmediate(resolve)); };
  view.render();
  assert.ok(texts.includes("Files") && texts.includes("Changes") && texts.includes("+"), "controls survive a hidden tab strip");
  assert.ok(texts.includes("Task"), "the current task title is always visible");
  await send("files");
  assert.equal(panel.hidden, false, "keyboard commands open Files while tabs are hidden");
  assert.equal(body.active, "files");
  view.render();
  active = { id: "space-two", name: "Project two", active: true };
  view.render(); view.render();
  assert.equal(panel.hidden, true, "a new space starts without another space's panel");
  await send("changes");
  view.render();
  active = { id: "space-one", name: "Project one", active: true };
  view.render(); view.render();
  assert.equal(body.active, "files", "returning restores this space's Files panel");
  await send("files");
  assert.equal(panel.hidden, true, "the same shortcut closes its open panel");
  await send("editor");
  assert.deepEqual(executions, [["zed", ["/workspace/one"]]], "Zed opens the focused terminal's folder");
  focus = { ...focus, terminal: "remote/fixture-terminal", cwd: "/remote/project" };
  await send("editor");
  assert.equal(executions.length, 1, "remote folders never open on the local machine");
  await view.openEditor({ cwd: null, remote: false });
  assert.equal(notices.length, 0, "an empty workspace does not try to launch an editor");
  await view.openEditor({ cwd: "/workspace/clicked", remote: false });
  assert.deepEqual(executions.at(-1), ["zed", ["/workspace/clicked"]], "a queued click keeps the folder selected when it was pressed");
  editorFails = true;
  await view.openEditor({ cwd: "/workspace/clicked", remote: false });
  assert.equal(notices[0]?.level, "error", "editor launch failures are visible");
}

console.log("Herdr mod fixtures passed: attention order, contextual rows, tab hiding, persistent controls, per-space panels and editor targeting.");
