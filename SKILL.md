---
name: openlist-skill
description: OpenList / AList 文件管理技能。用于浏览目录、搜索文件、获取直链、上传、改名、移动、复制、删除、分享和索引维护。适用于用户提到 OpenList、AList、网盘管理、文件同步或需要操作远程存储内容的场景。
---

# OpenList 文件管理

通过 `scripts/openlist.py` 调用 OpenList（AList 社区分支）HTTP API。以脚本实现为准，`references/api.md` 只作接口参考，不作为执行规则。

## 使用原则

1. 先发现，再修改。只读操作优先使用 `list`、`get`、`search`，写操作前先确认目标路径存在。
2. 不要臆造参数。只使用脚本里真实支持的命令和参数，不要补不存在的选项，也不要把参考文档当成脚本能力。
3. 避免破坏性尝试。`remove`、`rename`、`move`、`copy`、`index-build` 这类操作必须基于明确路径；当目标不明确时先列目录或获取文件信息。
4. 搜索失败时不要立刻重建索引。先换关键词，再 `list` 定位，最后才考虑 `index-update` 或 `index-build`。
5. 自动化场景优先输出 JSON。需要机器读取结果时使用 `--json`，仅在人工浏览时再用默认格式。

## 配置

脚本会从 `config.json` 读取配置，路径是 `scripts/../config.json`。支持两种方式：

1. OpenList 实例地址 + 用户名 / 密码，先 `login` 再保存 token。
2. OpenList 实例地址 + 现成 token，直接通过 `--token` 传入或写入配置。

如果参数中给了 `--url` 或 `--token`，优先使用参数值，不依赖配置文件。

## 命令速查

运行方式：`python scripts/openlist.py <command> [options]`

### 基础命令

| 命令 | 作用 | 必需参数 |
|------|------|----------|
| `login` | 登录并保存 token | `--url --username --password` |
| `list` | 列出目录内容 | `--path` |
| `get` | 获取文件或目录信息 | `--path` |
| `search` | 搜索文件 | `--keyword` |
| `mkdir` | 新建目录 | `--path` |
| `rename` | 重命名文件或目录 | `--path --new-name` |
| `move` | 移动文件或目录 | `--path --dst` |
| `copy` | 复制文件或目录 | `--path --dst` |
| `remove` | 删除文件或目录 | `--names` |
| `link` | 获取下载直链 | `--path` |
| `upload` | 上传文件 | `--path --file` |
| `batch-rename` | 批量重命名 | `--src-dir --rename-pairs` |
| `regex-rename` | 正则重命名 | `--src-dir --src-regex --dst-regex` |

### 分享命令

| 命令 | 作用 | 必需参数 |
|------|------|----------|
| `share-list` | 列出分享 | 无 |
| `share-create` | 创建分享 | `--files` |
| `share-get` | 获取分享信息 | `--id` |
| `share-update` | 更新分享 | `--id` |
| `share-delete` | 删除分享 | `--id` |

### 索引命令

| 命令 | 作用 |
|------|------|
| `index-progress` | 查看索引进度 |
| `index-update` | 增量更新索引 |
| `index-clear` | 清除索引 |
| `index-build` | 全量重建索引，最后手段 |

## 决策流程

### 目录浏览

1. 要看目录内容，先用 `list --path <dir> --json`。
2. 要确认单个对象是否存在或查看属性，用 `get --path <path>`。
3. 目录不明确时，先从父目录开始列，再逐层定位。

### 搜索

1. 先用 `search --path <root> --keyword <keyword>`。
2. 如果结果为空或明显不对，换更短、更模糊的关键词再试。
3. 再不行就用 `list` 逐级查找。
4. 只有在确认某个目录确实需要补索引时，才用 `index-update --paths <dir>`。
5. 只有索引损坏、首次配置或明确要求全量重建时，才用 `index-build`。

### 写操作

1. `rename`、`move`、`copy`、`remove` 前先确认完整路径。
2. 对于删除，必须确认是精确目标，不要用模糊名称代替完整路径。
3. 上传前确认目标路径是目录还是带文件名的完整目标路径。

## 关键参数说明

- `list` 支持 `--path`、`--page`、`--per-page`、`--refresh`。
- `search` 支持 `--path`、`--keyword`、`--page`、`--per-page`、`--max-depth`、`--no-api`。
- `upload` 支持 `--replace` 和 `--async-upload`。
- `remove` 的 `--names` 是逗号分隔的完整路径列表。
- `share-create` 使用 `--files`，不是 `--paths`。
- `share-get`、`share-update`、`share-delete` 统一使用 `--id`。
- `index-build` 支持 `--async`。
- `--json` 让输出保持机器可解析，`--quiet` 只保留核心结果。

## 推荐示例

```bash
python scripts/openlist.py list --path / --json
python scripts/openlist.py get --path /Quark
python scripts/openlist.py search --path /Quark --keyword report --json
python scripts/openlist.py link --path /Quark/video.mp4 --json
python scripts/openlist.py upload --path /Backup/ --file ./report.pdf --replace
python scripts/openlist.py share-create --files /Quark/report.pdf --json
python scripts/openlist.py index-update --paths /Quark --json
python scripts/openlist.py index-build --async --json
```

## 返回格式

成功示例：

```json
{"code": 200, "message": "success", "data": {...}}
```

失败示例：

```json
{"code": 400, "message": "error description", "data": null}
```

## 参考

完整端点、请求体和响应字段见 `references/api.md`。当你需要核对参数细节时再查它；如果脚本与文档不一致，以脚本当前实现为准。
