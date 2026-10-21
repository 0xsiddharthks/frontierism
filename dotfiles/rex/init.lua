-- Keep the muscle memory from Ghostty. Rex owns the sessions and panes;
-- claude, cw and codex still run normally inside them.
rex.bind("cmd+t", "client.tab.new")
rex.bind("cmd+w", "client.close")
rex.bind("cmd+shift+[", "client.tab.previous")
rex.bind("cmd+shift+]", "client.tab.next")
for n = 1, 9 do
  rex.bind("cmd+" .. n, "client.tab.goto", { index = n })
end
rex.bind("cmd+d", "pane.split", { direction = "right" })
rex.bind("cmd+shift+d", "pane.split", { direction = "down" })
rex.bind("cmd+shift+enter", "pane.zoom")
for _, direction in ipairs({ "left", "right", "up", "down" }) do
  rex.bind("cmd+alt+" .. direction, "pane.focus", { direction = direction })
end
rex.bind("cmd+shift+p", "client.palette.toggle")
rex.bind("cmd+f", "client.find.open")
rex.bind("cmd+up", "client.prompt.previous")
rex.bind("cmd+down", "client.prompt.next")
rex.bind("ctrl+cmd+s", "session.switch")

-- Read the foreground process's directory, including the worktree cw entered.
-- A shell's last reported directory may still be the original checkout.
local function working_directory(ctx, args)
  if args.cwd then return args.cwd end
  if not ctx.block_id then
    error("Choose a terminal first, or pass cwd=/absolute/project/path", 0)
  end
  local process, err = rex.block.call("com.superlogical.terminal", "process", {
    block_id = ctx.block_id,
  })
  if not process then error(err, 0) end
  if process.foreground and process.foreground.cwd then
    return process.foreground.cwd
  end
  error("Cannot read the focused program's directory; pass cwd=/absolute/project/path", 0)
end

local function agent_tab(name, title, program, key)
  rex.action{
    name = name,
    title = title .. " in Current Directory",
    category = "Coding Agents",
    args = { cwd = "string?" },
    run = function(ctx, args)
      local window, err = rex.session.new_window{
        window_label = title,
        layout = rex.layout.block{
          flavor = "com.superlogical.terminal.shell",
          options = {
            cwd = working_directory(ctx, args),
            -- Start through a normal shell so job control and directory
            -- tracking keep working when the agent takes the foreground.
            initial_input = program .. "\n",
          },
        },
      }
      if not window then error(err, 0) end
      return window
    end,
  }
  rex.bind(key, name)
end

agent_tab("claude_tab", "Claude Code", "claude", "ctrl+cmd+c")
agent_tab("codex_tab", "Codex", "codex", "ctrl+cmd+x")

-- Machine-specific hosts and other private settings belong outside this repo.
-- Keep personal key bindings here too if they should override the shared ones.
local private = (os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config"))
  .. "/rex/private.lua"
local file = io.open(private, "r")
if file then
  file:close()
  dofile(private)
end
