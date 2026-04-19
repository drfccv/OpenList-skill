# OpenList API 参考

> OpenList API 与 AList v3 API 兼容。
> 基础 URL: `<base_url>/api`

## 认证

### 登录
```
POST /api/auth/login
Content-Type: application/json

{"username": "admin", "password": "your-password", "otp_code": ""}

Response 200:
{"code": 200, "message": "success", "data": {"token": "eyJhbGci..."}}
```

> Token 直接放在请求头 `Authorization` 中，**不要 Bearer 前缀**。
> 用户名/密码由部署 OpenList 的管理员提供。

## 文件系统

### 列出目录
```
POST /api/fs/list
Authorization: <token>
Content-Type: application/json

{"path": "/", "page": 1, "per_page": 50, "refresh": false}

Response 200:
{
  "code": 200,
  "data": {
    "content": [
      {
        "name": "Document",
        "size": 0,
        "is_dir": true,
        "modified": "2024-01-01T00:00:00Z",
        "created": "2024-01-01T00:00:00Z",
        "sign": "",
        "thumb": "",
        "type": 0,
        "raw_url": "",
        "provider": "Local",
        "hash_info": null
      }
    ],
    "total": 10,
    "readme": "",
    "write": false,
    "navigate": [],
    "uploading": []
  }
}
```

### 获取文件/目录信息
```
POST /api/fs/get
Authorization: <token>
Content-Type: application/json

{"path": "/path/to/file.txt"}

Response 200:
{"code": 200, "message": "success", "data": {"name": ..., "size": ..., "is_dir": ..., "provider": "..."}}
```

### 搜索
```
POST /api/fs/search
Authorization: <token>
Content-Type: application/json

{"parent": "/", "keywords": "filename", "scope": 1, "page": 1, "per_page": 20}

Response 200:
{
  "code": 200,
  "data": {
    "content": [
      {"name": "report.pdf", "path": "/Documents/report.pdf", "size": 1234, "is_dir": false, "modified": "..."}
    ],
    "total": 1
  }
}
```

> 搜索依赖搜索索引，首次使用需调用 `POST /api/admin/index/build` 构建索引。
> 部分存储后端（如 139Yun / 中国移动云盘）不支持文件枚举，无法建立索引，搜索无法覆盖。

### 新建目录
```
POST /api/fs/mkdir
Authorization: <token>
Content-Type: application/json

{"path": "/path/to/newfolder"}

Response 200:
{"code": 200, "message": "success", "data": null}
```

### 重命名
```
POST /api/fs/rename
Authorization: <token>
Content-Type: application/json

{"path": "/old.txt", "name": "new.txt"}

Response 200:
{"code": 200, "message": "success", "data": null}
```

### 批量重命名
```
POST /api/fs/batch_rename
Authorization: <token>
Content-Type: application/json

{
  "src_dir": "/folder",
  "rename_objects": [
    {"src_name": "old1.txt", "new_name": "new1.txt"},
    {"src_name": "old2.txt", "new_name": "new2.txt"}
  ]
}

Response 200:
{"code": 200, "message": "success", "data": null}
```

### 正则重命名
```
POST /api/fs/regex_rename
Authorization: <token>
Content-Type: application/json

{
  "src_dir": "/folder",
  "src_name_regex": "^(.*)\\.txt$",
  "new_name_regex": "$1_renamed.txt"
}

Response 200:
{"code": 200, "message": "success", "data": null}
```

> `src_name_regex` 是正则表达式，`new_name_regex` 是替换模式（支持 `$1`, `$2` 等捕获组）。

### 移动
```
POST /api/fs/move
Authorization: <token>
Content-Type: application/json

{"src_dir": "/", "dst_dir": "/Backup", "names": ["file.txt"]}

Response 200:
{"code": 200, "message": "success", "data": null}
```

> `names` 是文件名数组，不包含路径。路径由 `src_dir` 指定。

### 复制
```
POST /api/fs/copy
Authorization: <token>
Content-Type: application/json

{"src_dir": "/", "dst_dir": "/Backup", "names": ["file.txt"]}

Response 200:
{"code": 200, "message": "success", "data": null}
```

> `names` 是文件名数组，不包含路径。路径由 `src_dir` 指定。

### 删除
```
POST /api/fs/remove
Authorization: <token>
Content-Type: application/json

{"names": ["/Quark/file.txt", "/Quark/another.txt"]}

Response 200:
{"code": 200, "message": "success", "data": null}
```

> `names` 是**完整路径**数组，包含目录前缀。

### 获取直链
```
POST /api/fs/link
Authorization: <token>
Content-Type: application/json

{"path": "/file.txt", "method": "GET"}

Response 200:
{
  "code": 200,
  "message": "success",
  "data": {
    "raw_url": "https://...",
    "expires": "2024-01-01T00:00:00Z",
    "sign": "..."
  }
}
```

### 表单上传
```
PUT /api/fs/form
Authorization: <token>
Content-Type: multipart/form-data
File-Path: /dest/file.txt

file: <binary>

Response 200:
{"code": 200, "message": "success", "data": null}
```

> `File-Path` 放在请求头中，需要 URL 编码非 ASCII 字符。
> 可选请求头：`Overwrite: true`（覆盖已存在文件）、`As-Task: true`（异步上传）。

### 流式上传
```
PUT /api/fs/put
Authorization: <token>
Content-Type: application/octet-stream
File-Path: /dest/file.txt

<binary data>

Response 200:
{"code": 200, "message": "success", "data": null}
```

### 分块上传（>5MB）
```
# 1. 初始化
POST /api/fs/multipart
Authorization: <token>
Content-Type: application/json

{"path": "/dest/large.zip", "temp_path": false}

# Response
{"code": 200, "data": {"upload_id": "uuid-..."}}

# 2. 上传分块
POST /api/fs/put
Authorization: <token>
Content-Type: multipart/form-data

path: /dest/large.zip
file: <binary>
upload_id: uuid-...
part_number: 1

# 3. 完成分块上传
POST /api/fs/multipart_done
Authorization: <token>
Content-Type: application/json

{"path": "/dest/large.zip", "name": "large.zip", "upload_id": "uuid-...", "upload_id_signature": "..."}
```

## 分享管理

### 列出分享
```
POST /api/share/list
Authorization: <token>
Content-Type: application/json

{"page": 1, "per_page": 30}

Response 200:
{
  "code": 200,
  "message": "success",
  "data": {
    "content": [
      {
        "id": "NxEzmQop",
        "expires": null,
        "pwd": "",
        "accessed": 0,
        "max_accessed": 0,
        "disabled": false,
        "remark": "",
        "files": ["/Quark/document.pdf"],
        "creator": "admin",
        "creator_role": 2
      }
    ],
    "total": 1
  }
}
```

> 分享链接格式：`<base_url>/@s/<id>`

### 获取分享详情
```
GET /api/share/get?id=<share_id>
Authorization: <token>

Response 200:
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "NxEzmQop",
    "expires": null,
    "pwd": "",
    "files": ["/Quark/document.pdf"],
    ...
  }
}
```

### 创建分享
```
POST /api/share/create
Authorization: <token>
Content-Type: application/json

{
  "files": ["/Quark/document.pdf", "/Quark/folder"],
  "pwd": "optional-password",
  "expires": "2024-12-31T23:59:59+08:00"
}

Response 200:
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "NxEzmQop",
    "files": ["/Quark/document.pdf"],
    "expires": "2024-12-31T23:59:59+08:00",
    "pwd": "optional-password",
    ...
  }
}
```

> `files` 是文件/文件夹的完整路径数组。
> `pwd` 可选，设置访问密码。
> `expires` 可选，过期时间（ISO 8601 格式，含时区）。

### 更新分享
```
POST /api/share/update
Authorization: <token>
Content-Type: application/json

{
  "share_id": "NxEzmQop",
  "password": "new-password",
  "expire_at": "2024-12-31T23:59:59+08:00"
}

Response 200:
{"code": 200, "message": "success", "data": null}
```

### 删除分享
```
POST /api/share/delete?id=<share_id>
Authorization: <token>

Response 200:
{"code": 200, "message": "success", "data": null}
```

## 搜索索引管理

### 构建搜索索引
```
POST /api/admin/index/build
Authorization: <token>

{}
```
> 需管理员权限。

### 更新搜索索引
```
POST /api/admin/index/update
Authorization: <token>
Content-Type: application/json

{"paths": ["/Quark", "/Local"]}

Response 200:
{"code": 200, "message": "success", "data": null}
```

> `paths` 为空数组时更新所有存储的索引。需管理员权限。

### 清除搜索索引
```
POST /api/admin/index/clear
Authorization: <token>

{}

Response 200:
{"code": 200, "message": "success", "data": null}
```

> 删除所有搜索索引数据。需管理员权限。

### 检查索引状态
```
GET /api/admin/index/progress
Authorization: <token>

# Response
{
  "code": 200,
  "data": {
    "obj_count": 2575,
    "is_done": true,
    "last_done_time": "2026-04-19T19:49:27+08:00",
    "error": ""
  }
}
```

## 状态码

| code | 说明 |
|------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 / token 无效 |
| 403 | 无权限 |
| 404 | 文件/目录不存在 |
| 500 | 服务器内部错误 |
