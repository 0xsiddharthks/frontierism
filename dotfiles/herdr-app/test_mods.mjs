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
  assert.equal(strip.hidden, false, "the empty window keeps its new-tab controls");
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
  assert.equal(texts.filter(text => text === "Fixture Agent").length, 4, "each row has an agent-name line");
  for (const symbol of ["!", "~", "✓", "○"]) assert.ok(texts.includes(symbol), "each status has its own symbol");
}

console.log("Herdr mod fixtures passed: priority, two-line rows, symbols, single-tab hide and restore.");
