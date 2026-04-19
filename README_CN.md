# OpenList 技能

AI Agent 文件管理技能，通过 HTTP API 操作 [OpenList](https://github.com/OpenListTeam/OpenList)（AList 社区分支）实例。

[English](README.md)

## 功能

让 AI Agent 具备浏览、上传、下载、搜索、分享、整理云盘文件的能力，如同操作本地文件系统。

触发场景：用户提到 OpenList、AList、云盘管理、远程文件浏览、网络存储等。

## 命令一览（21 个）

### 文件操作

| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `login` | 登录并保存 token | `--url --username --password` |
| `list` | 列出目录内容 | `--path` |
| `get` | 获取文件/目录信息 | `--path` |
| `search` | 按关键词搜索 | `--keyword` |
| `mkdir` | 新建文件夹 | `--path` |
| `rename` | 重命名 | `--path --new-name` |
| `move` | 移动文件 | `--path --dst` |
| `copy` | 复制文件 | `--path --dst` |
| `remove` | 删除文件 | `--names` |
| `link` | 获取下载直链 | `--path` |
| `upload` | 上传本地文件 | `--path --file` |

### 批量操作

| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `batch-rename` | 批量重命名 | `--src-dir --rename-pairs` |
| `regex-rename` | 正则替换重命名 | `--src-dir --src-regex --dst-regex` |

### 分享管理

| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `share-list` | 列出所有分享 | — |
| `share-create` | 创建分享链接 | `--paths` |
| `share-get` | 获取分享详情 | `--ids` |
| `share-update` | 更新分享设置 | `--id` |
| `share-delete` | 删除分享 | `--ids` |

### 索引管理

| 命令 | 功能 |
|------|------|
| `index-build` | 重建搜索索引（慎用，耗时长） |
| `index-update` | 增量更新索引 `--paths` |
| `index-clear` | 清除索引 |
| `index-progress` | 查看索引进度 |

## 配置

### 前置要求

- Python 3.6+
- `requests` 库
- 有访问权限的 OpenList/AList 实例

### 方式 A：自动登录（推荐）

```bash
python scripts/openlist.py login --url https://your-instance.example.com --username admin --password secret
```

自动在脚本同级目录生成 `config.json`，后续无需重复传入。

### 方式 B：命令行参数

```bash
python scripts/openlist.py list --url https://your-instance.example.com --token xxx --path /
```

每次调用传入 `--url` 和 `--token`，无需配置文件。

## Agent 使用守则

### 搜索无结果时的处理

**禁止自动触发 `index-build`**，按以下顺序排查：

1. 更换关键词（模糊匹配、部分文件名、不同扩展名）
2. 用 `list` 浏览目标目录手动定位
3. 用 `index-update --paths "/目标目录"` 增量更新
4. 仅当索引损坏或首次配置时才使用 `index-build`

### 分享链接

分享链接格式为 `http://<host>/@s/<id>`，`share-create` 返回中包含 `share_link` 字段。

### 返回格式

所有命令返回 JSON：

```json
// 成功
{"code": 200, "message": "success", "data": {...}}

// 失败
{"code": 400, "message": "error description", "data": null}
```

## 项目结构

```
openlist-skill/
├── SKILL.md              # 技能描述文件（Agent 运行时读取）
├── scripts/
│   └── openlist.py       # 核心脚本，所有命令入口
├── references/
│   └── api.md            # 完整 API 参考文档
└── config.json           # 自动生成的凭据文件（已 gitignore）
```

## 许可证

MIT
