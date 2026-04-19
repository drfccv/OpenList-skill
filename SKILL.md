---
name: openlist
description: OpenList / AList 文件管理技能。通过 OpenList 实例进行文件浏览、上传、下载、改名、移动、复制、删除、搜索等操作。触发场景：用户提到 OpenList、AList、云盘管理、文件同步、需要浏览远程存储文件等。
---

# OpenList 文件管理

OpenList（AList 社区分支）HTTP API 封装，通过 Python 脚本调用。

## 前置配置

使用前需要以下信息之一：
1. OpenList 实例地址 + 用户名/密码（自动登录获取 token）
2. OpenList 实例地址 + 已有 token

配置自动存于脚本同级目录的 `config.json`（即 `scripts/../config.json`）。无需手动创建，首次使用时自动生成。也可通过 `--url` 和 `--token` 参数直接传入，跳过配置文件。

## 命令速查

```bash
python scripts/openlist.py <command> [options]
```

| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `login` | 登录获取 token | `--url --username --password` |
| `list` | 列出目录 | `--path` |
| `get` | 获取文件信息 | `--path` |
| `search` | 搜索文件 | `--keyword` |
| `mkdir` | 新建文件夹 | `--path` |
| `rename` | 重命名 | `--path --new-name` |
| `move` | 移动文件 | `--path --dst` |
| `copy` | 复制文件 | `--path --dst` |
| `remove` | 删除文件 | `--names` |
| `link` | 获取直链 | `--path` |
| `upload` | 上传文件 | `--path --file` |
| `batch-rename` | 批量重命名 | `--src-dir --rename-pairs` |
| `regex-rename` | 正则重命名 | `--src-dir --src-regex --dst-regex` |

### 分享管理命令

| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `share-list` | 列出分享 | 无 |
| `share-create` | 创建分享 | `--paths` |
| `share-get` | 获取分享信息 | `--ids` |
| `share-update` | 更新分享 | `--id` |
| `share-delete` | 删除分享 | `--ids` |

### 索引管理命令

| 命令 | 功能 |
|------|------|
| `index-build` | 构建搜索索引（慎用，耗时长） |
| `index-update` | 更新索引 `--paths` |
| `index-clear` | 清除索引 |
| `index-progress` | 查看索引进度 |

**⚠️ 索引操作原则：**
- `index-build` 重建全部索引，耗时且资源密集，**仅在首次配置或索引损坏时使用**
- 搜索无结果时，**优先尝试**：
  1. 更换关键词（模糊匹配、部分文件名）
  2. 用 `list` 浏览目录定位
  3. 用 `index-update --paths "/目标目录"` 增量更新
- **避免自动触发 `index-build`**

## 全局参数

- `--url <url>` — 覆盖配置中的实例地址
- `--token <token>` — 覆盖配置中的 token
- `--json` — 输出纯 JSON
- `--quiet` — 仅输出核心数据

## 使用示例

```bash
# 浏览文件
python scripts/openlist.py list --path /
python scripts/openlist.py list --path /Quark --page 1 --per-page 20

# 下载文件（获取直链）
python scripts/openlist.py link --path /Quark/video.mp4

# 上传文件
python scripts/openlist.py upload --path /Backup/ --file ./report.pdf --replace

# 批量重命名
python scripts/openlist.py batch-rename --src-dir /Quark --rename-pairs "old1.txt:new1.txt,old2.txt:new2.txt"

# 正则重命名：所有 .txt 改为 .md
python scripts/openlist.py regex-rename --src-dir /Quark --src-regex "^(.*)\.txt$" --dst-regex "$1.md"

# 创建分享
python scripts/openlist.py share-create --paths "/Quark/report.pdf"
# 返回: {"code": 200, "data": {"id": "xxx", "share_link": "http://.../@s/xxx"}}

# 搜索无结果时的处理流程
# 1. 先尝试换关键词
python scripts/openlist.py search --path /Quark --keyword "report"
python scripts/openlist.py search --path /Quark --keyword "pdf"
# 2. 用 list 浏览目录定位
python scripts/openlist.py list --path /Quark --page 1 --per-page 50
# 3. 确认文件存在后增量更新索引（而非重建）
python scripts/openlist.py index-update --paths "/Quark"
# 4. 最后才考虑 index-build（仅当索引损坏或首次配置）
```

## 返回格式

成功：
```json
{"code": 200, "message": "success", "data": {...}}
```

失败：
```json
{"code": 400, "message": "error description", "data": null}
```

## 详细 API 参考

完整端点、请求体、响应格式见 `references/api.md`。
