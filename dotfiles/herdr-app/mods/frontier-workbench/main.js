// Persistent workspace context and controls, independent of the tab strip.
import { View, div, svg, image } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { spaces, panes, focused, layout, run, theme, window, home, openOverlay, nextCommand, exec, notify } from "herdr";

const clean = (text) => (text ?? "").replace(/^[^\p{L}\p{N}]+/u, "").trim();

function find(node, id) {
  if (node?.id === id) return node;
  for (const child of node?.children ?? []) {
    const result = find(child, id);
    if (result) return result;
  }
  return null;
}

function folder(path) {
  const h = home();
  return path === h ? "~" : path?.startsWith(h + "/") ? "~" + path.slice(h.length) : path ?? "";
}

export default class Workbench extends View {
  init(_props, cx) {
    try { this.panels = JSON.parse(localStorage.getItem("panels") ?? "{}"); }
    catch { this.panels = {}; }
    cx.spawn(async (cx) => {
      for (;;) {
        const command = await nextCommand();
        if (command === "files" || command === "changes") this.togglePanel(command);
        else if (command === "editor") await this.openEditor();
        cx.notify();
      }
    });
  }

  context() {
    const focus = focused();
    const space = spaces().find(s => s.active);
    const pane = panes().find(p => p.pane === focus?.pane);
    return {
      space, pane,
      cwd: focus?.cwd || pane?.cwd || space?.folder,
      remote: Boolean(space?.machine || focus?.terminal?.includes("/")),
    };
  }

  // Adapted from the shipped tabs mod. Keeping this in a visible block also
  // makes panel restoration and keyboard commands work with the strip hidden.
  syncPanel(space) {
    const panel = find(layout(), "panel"), body = find(layout(), "panel-body");
    if (!space || !panel) return;
    const now = panel.hidden ? null : body?.active ?? null;
    if (space.id !== this.space) {
      const first = this.space === undefined;
      this.space = space.id; this.pending = null;
      if (!(first && !(space.id in this.panels))) {
        const saved = this.panels[space.id];
        const want = saved === "files" || saved === "changes" ? saved : null;
        if (want !== now) {
          this.pending = { want, until: Date.now() + 1000 };
          if (want) { run("layout.select", { stack: "panel-body", child: want }); run("layout.show", { id: "panel" }); }
          else run("layout.hide", { id: "panel" });
          return;
        }
      }
    }
    if (this.pending) {
      if (this.pending.want !== now && Date.now() < this.pending.until) return;
      this.pending = null;
    }
    if (this.panels[space.id] === now) return;
    this.panels[space.id] = now;
    localStorage.setItem("panels", JSON.stringify(this.panels));
  }

  togglePanel(id) {
    const panel = find(layout(), "panel"), body = find(layout(), "panel-body");
    if (!panel || !body) return;
    if (!panel.hidden && body.active === id) run("layout.hide", { id: "panel" });
    else {
      run("layout.select", { stack: "panel-body", child: id });
      run("layout.show", { id: "panel" });
    }
  }

  async openEditor(context = this.context()) {
    const { cwd, remote } = context;
    if (!cwd || remote) return;
    try {
      const result = await exec("zed", [cwd]);
      if (result.code !== 0) throw new Error(result.stderr || "Zed could not open the folder.");
    } catch (error) {
      notify({ title: "Could not open Zed", body: String(error), level: "error" });
    }
  }

  render() {
    const t = theme();
    const { space, pane, cwd, remote } = this.context();
    this.syncPanel(space);
    const program = pane?.program;
    const title = clean(pane?.title) || program?.name || space?.name || "Choose a space";
    const detail = [...new Set([program?.name, folder(cwd), pane?.branch].filter(Boolean))].join(" · ");
    const panel = find(layout(), "panel"), body = find(layout(), "panel-body");
    const stop = (_event, cx) => cx.stop_propagation();
    const button = (id, label, hint, action, active = false) =>
      h_flex().id(id).h(27).px(9).flex_none().items_center().rounded(5).text_size(12)
        .bg(active ? t.selected : t.chrome).text_color(active ? t.foreground : t.muted)
        .hover(s => s.bg(t.hover).text_color(t.foreground)).tooltip(hint)
        .on_mouse_down("left", stop).on_click(action).child(label);
    const panelButton = (id, label, hint) => button(`workbench-${id}`, label, hint,
      () => this.togglePanel(id), panel && !panel.hidden && body?.active === id);
    return h_flex().id("workbench").size_full().min_w(0).px(12).gap(6).items_center()
      .bg(t.chrome).border_b(1).border_color(t.border)
      .when(Boolean(program?.icon), el => el.child(program.tint
        ? svg(program.icon).size(16).flex_none().text_color(t.muted)
        : image(program.icon).size(16).flex_none()))
      .when(Boolean(pane?.status), el => el.child(div().w(14).flex_none().text_center()
        .text_color(t[pane.status] ?? t.dim)
        .child(({ blocked: "!", working: "~", done: "✓", idle: "○" })[pane.status] ?? "?")))
      .child(v_flex().flex_1().min_w(0).gap(1).tooltip([title, detail].filter(Boolean).join("\n"))
        .child(div().truncate().text_size(12.5).font_medium().text_color(t.foreground).child(title))
        .when(Boolean(detail), el => el.child(div().truncate().text_size(10.5).text_color(t.dim).child(detail))))
      .child(panelButton("files", "Files", "Files · Cmd+Shift+E"))
      .child(panelButton("changes", "Changes", "Changes · Cmd+Shift+G"))
      .when(Boolean(cwd) && !remote, el => el.child(button("workbench-editor", "Zed", "Open this folder in Zed · Cmd+Shift+O",
        (_event, cx) => {
          const context = this.context();
          cx.spawn(async (cx) => { await this.openEditor(context); cx.notify(); });
        })))
      .child(button("workbench-new", "+", space ? "New terminal or agent · Cmd+T creates a terminal" : "New space · Cmd+N",
        () => {
          if (space) openOverlay({ mod: "new-menu", kind: "popup", width: 250, height: 512 });
          else run("space.new");
        }))
      .when(window()?.buttons, el => el
        .child(button("workbench-minimize", "−", "Minimize", () => run("window.minimize")))
        .child(button("workbench-maximize", "□", "Maximize", () => run("window.maximize")))
        .child(button("workbench-close", "×", "Close window", () => run("window.close"))));
  }
}
