# Agent Studio Installer

Install the workshop `studio_shell/` UI into a student agent project.

Left column: student-designed Streamlit pages. Right column: `agent_core.py` chat panel.

## Usage

From the project where you want to add the shell:

```powershell
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell
```

Local development:

```powershell
uvx --from . add-studio-shell
```

Require `agent_core.py` during installation:

```powershell
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell --require-agent-core
```

Update an existing shell while keeping student work:

```powershell
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell --update
```

By default, installation and update also run:

```powershell
uv add streamlit "openai-tts @ git+https://github.com/mz038197/openai-tts.git"
```

Skip dependency changes:

```powershell
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell --no-install-deps
```

`--update` preserves:

- `studio_shell/workspace/`（含 `user_settings.json`）
- `studio_shell/pages/`（學生自訂頁面與修改）
- `studio_shell/sessions/`
- `studio_shell/scripts/`
- `studio_shell/uploads/`

After installation:

```powershell
uv run streamlit run studio_shell/app.py
```

## TTS settings

The right-side Agent panel reads and writes TTS preferences at:

```text
studio_shell/workspace/user_settings.json
```

The file is created automatically with defaults when the panel opens. It uses these keys:

```json
{
  "tts_enabled": false,
  "tts_voice": "nova",
  "tts_instructions": "用台灣繁體中文說話。",
  "tts_speed": 1.0
}
```

Settings are loaded in this order:

1. `studio_shell/workspace/user_settings.json`
2. `.env` values read by `openai-tts` (`TTS_VOICE`, `TTS_INSTRUCTIONS`, `TTS_SPEED`)
3. `openai-tts` built-in defaults

Use the **重新載入設定** button in the TTS panel after manually editing `user_settings.json`.
The TTS panel is available even before Agent Core is connected.

## Classroom exercises

See `docs/exercises.md` in this repo for guided left-column + Agent context practice.

## What It Does

- Copies `studio_shell/` into the current project.
- Connects the right panel to `agent_core.py` (no CSV required).
- Persists TTS preferences to `studio_shell/workspace/user_settings.json` across page changes and browser restarts.
- Installs `streamlit` and `openai-tts` by default.
- Refuses to overwrite an existing shell unless `--force` is used.
- Supports `--update` to refresh shell core while preserving student pages and workspace.
