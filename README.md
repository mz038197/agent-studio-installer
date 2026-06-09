# Agent Studio Installer

Install the workshop `studio_shell/` UI into a student agent project.

Left column: student-designed Streamlit pages. Right column: `peas-agent-core` chat panel.

## Usage

From the project where you want to add the shell:

```powershell
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell
```

Local development:

```powershell
uvx --from . add-studio-shell
```

Require `peas-agent-core` during installation:

```powershell
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell --require-agent-core
```

Update an existing shell while keeping student work:

```powershell
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell --update
```

By default, installation and update also run:

```powershell
uv add --upgrade-package openai-tts streamlit "openai-tts @ git+https://github.com/mz038197/openai-tts.git" "peas-agent-core @ git+https://github.com/mz038197/peas-agent-core.git@v0.1.1"
```

Skip dependency changes:

```powershell
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell --no-install-deps
```

`--update` preserves:

- `studio_shell/pages/`（學生自訂頁面與修改）
- `studio_shell/scripts/`
- `studio_shell/uploads/`
- legacy `studio_shell/workspace/`、`studio_shell/sessions/`（若舊專案仍有）

Agent runtime data lives under `~/.peas-agent/` and is **not** touched by `--update`.

After installation:

```powershell
# 1. Edit LLM settings
notepad $env:USERPROFILE\.peas-agent\config.json

# 2. (Optional) Edit TTS settings
notepad $env:USERPROFILE\.peas-agent\tts.json

# 3. Run Studio
uv run streamlit run studio_shell/app.py
```

## Agent configuration

Studio and CLI share `~/.peas-agent/`:

```text
~/.peas-agent/
├── config.json          # LLM: api_key, model, temperature, base_url
├── tts.json             # TTS: api_key, voice, instructions, speed
└── workspace/
    ├── sessions/        # chat history (*.jsonl)
    ├── memory/
    ├── skills/
    ├── tools/           # custom LangChain tools
    └── uploads/chat_images/
```

**config.json** example:

```json
{
  "workspace": "~/.peas-agent/workspace",
  "token_budget": 100000,
  "llm": {
    "api_key": "sk-...",
    "model": "gpt-5.4-mini",
    "temperature": 0.2,
    "base_url": ""
  }
}
```

## TTS settings

TTS preferences are stored at `~/.peas-agent/tts.json` (not in the project):

```json
{
  "api_key": "",
  "base_url": "",
  "enabled": false,
  "voice": "nova",
  "instructions": "用台灣繁體中文說話。",
  "speed": 1.0
}
```

The right-side panel reads and writes this file. TTS uses **only** `tts.json` — no fallback to `config.json` or project `.env`.

On first start, legacy `studio_shell/workspace/user_settings.json` is migrated automatically.

## Update vs force

```powershell
# Correct: refresh shell core, keep student pages
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell --update

# Dangerous: backs up and replaces entire studio_shell/
uvx --from git+https://github.com/mz038197/agent-studio-installer.git add-studio-shell --force
```

**Naming tip:** put custom pages in new files like `pages/4_MyDashboard.py`; avoid editing built-in `1_`–`3_` pages so `--update` won't overwrite your work.

## Migration checklist (existing projects)

1. Set `~/.peas-agent/config.json` (`llm.api_key`) and `tts.json` (`api_key` for voice)
2. Use `--update`, not `--force`
3. Restart Streamlit → click「啟用 Agent」
4. Old sessions in `studio_shell/sessions/` are copied to `~/.peas-agent/workspace/sessions/` on first start
5. You can delete project-root `agent_core.py` — Studio now uses `peas-agent-core`

## Classroom exercises

See `docs/exercises.md` in this repo for guided left-column + Agent context practice.

## What It Does

- Copies `studio_shell/` into the current project.
- Connects the right panel to `peas-agent-core` via `Agent.create()`.
- Persists chat sessions and agent memory under `~/.peas-agent/workspace/`.
- Persists TTS preferences to `~/.peas-agent/tts.json`.
- Installs `streamlit`, `openai-tts`, and `peas-agent-core` by default.
- Refuses to overwrite an existing shell unless `--force` is used.
- Supports `--update` to refresh shell core while preserving student pages.
