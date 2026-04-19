# OpenList Skill

An AI agent skill for managing files on [OpenList](https://github.com/OpenListTeam/OpenList) (AList community fork) instances via HTTP API.

[中文文档](README_CN.md)

## What It Does

Gives an AI agent the ability to browse, upload, download, search, share, and organize files on any OpenList/AList server — as if operating a local filesystem.

Triggers when the user mentions OpenList, AList, cloud drive management, remote file browsing, or needs to interact with a network-attached storage instance.

## Commands (21)

### File Operations

| Command | Description | Required Args |
|---------|-------------|---------------|
| `login` | Authenticate and store token | `--url --username --password` |
| `list` | List directory contents | `--path` |
| `get` | Get file/directory metadata | `--path` |
| `search` | Search files by keyword | `--keyword` |
| `mkdir` | Create directory | `--path` |
| `rename` | Rename file or directory | `--path --new-name` |
| `move` | Move files between directories | `--path --dst` |
| `copy` | Copy files between directories | `--path --dst` |
| `remove` | Delete files | `--names` |
| `link` | Get direct download URL | `--path` |
| `upload` | Upload a local file | `--path --file` |

### Batch Operations

| Command | Description | Required Args |
|---------|-------------|---------------|
| `batch-rename` | Rename multiple files | `--src-dir --rename-pairs` |
| `regex-rename` | Rename via regex substitution | `--src-dir --src-regex --dst-regex` |

### Share Management

| Command | Description | Required Args |
|---------|-------------|---------------|
| `share-list` | List all shares | — |
| `share-create` | Create a share link | `--paths` |
| `share-get` | Get share details | `--ids` |
| `share-update` | Update share settings | `--id` |
| `share-delete` | Delete shares | `--ids` |

### Index Management

| Command | Description |
|---------|-------------|
| `index-build` | Rebuild search index (heavy, use sparingly) |
| `index-update` | Incremental index update `--paths` |
| `index-clear` | Clear search index |
| `index-progress` | Check indexing progress |

## Setup

### Prerequisites

- Python 3.6+
- `requests` (`pip install requests`)
- An OpenList/AList instance with valid credentials

### Configuration

**Option A — Auto-login (recommended):**

```bash
python scripts/openlist.py login --url https://your-instance.example.com --username admin --password secret
```

Creates `config.json` next to the script automatically. Subsequent calls use saved credentials.

**Option B — Inline parameters:**

```bash
python scripts/openlist.py list --url https://your-instance.example.com --token xxx --path /
```

No config file needed; pass `--url` and `--token` each time.

## Agent Guidelines

### Search Failure Workflow

When `search` returns no results, follow this order — **never auto-trigger `index-build`**:

1. Try alternate keywords (partial name, different extension)
2. Use `list` to browse the directory and locate the file manually
3. Use `index-update --paths "/target/dir"` for incremental update
4. Only use `index-build` if the index is corrupted or this is first-time setup

### Share Links

Share URLs follow the format `http://<host>/@s/<id>`. The `share-create` response includes a `share_link` field.

### Output Format

All commands return JSON:

```json
// Success
{"code": 200, "message": "success", "data": {...}}

// Failure
{"code": 400, "message": "error description", "data": null}
```

## Project Structure

```
openlist-skill/
├── SKILL.md              # Skill descriptor (read by agent runtime)
├── scripts/
│   └── openlist.py       # Core script — single entry point for all commands
├── references/
│   └── api.md            # Full API reference (endpoints, request/response schemas)
└── config.json           # Auto-generated credentials (gitignored)
```

## License

MIT
