#!/usr/bin/env python3
"""
OpenList API Python Wrapper
Usage: python openlist.py <command> [options]

Commands:
    login, list, get, mkdir, rename, move, copy, remove, search, link, upload

Run with --help for full usage.
"""
import argparse
import json
import os
import sys
import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

# ─── Config ────────────────────────────────────────────────────────────────────

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

# ─── HTTP helper ───────────────────────────────────────────────────────────────

def api_request(url, token, path, payload, method="POST", query_params=None):
    headers = {}
    if token:
        headers["Authorization"] = token
    if method == "GET":
        resp = requests.get(f"{url}{path}", headers=headers, timeout=30, params=query_params)
    else:
        resp = requests.post(f"{url}{path}", json=payload, headers=headers, timeout=30, params=query_params)
    resp.encoding = "utf-8"
    try:
        return resp.json()
    except Exception:
        return {"code": 999, "message": resp.text[:200]}

def api_upload(url, token, file_path, local_file, as_task=False, overwrite=True):
    """Upload file using PUT /api/fs/form (multipart form data)."""
    from urllib.parse import quote
    
    headers = {"Authorization": token}
    filename = os.path.basename(local_file)
    
    # File-Path goes in header - URL encode for non-ASCII characters
    # Use UTF-8 encoding with safe chars preserved
    encoded_path = quote(file_path, safe="/")
    headers["File-Path"] = encoded_path
    if as_task:
        headers["As-Task"] = "true"
    if overwrite:
        headers["Overwrite"] = "true"
    
    with open(local_file, "rb") as f:
        files = {"file": (filename, f)}
        resp = requests.put(
            f"{url}/api/fs/form",
            files=files,
            headers=headers,
            timeout=300
        )
    resp.encoding = "utf-8"
    try:
        return resp.json()
    except Exception:
        return {"code": 999, "message": f"Empty response: {resp.status_code}", "data": resp.text[:200]}

# ─── Commands ──────────────────────────────────────────────────────────────────

def cmd_login(args):
    url = args.url.rstrip("/")
    resp = requests.post(
        f"{url}/api/auth/login",
        json={"username": args.username, "password": args.password},
        timeout=15
    )
    resp.encoding = "utf-8"
    result = resp.json()
    if result.get("code") == 200:
        token = result["data"]["token"]
        cfg = {"base_url": url, "username": args.username, "password": args.password, "token": token}
        save_config(cfg)
        _output(args, {"message": "Login OK, token saved.", "token": token})
    else:
        _output(args, result)

def cmd_list(args):
    url, token = _resolve(args)
    result = api_request(url, token, "/api/fs/list", {
        "path": args.path or "/",
        "page": args.page,
        "per_page": args.per_page,
        "refresh": args.refresh
    })
    _output(args, result)

def cmd_get(args):
    url, token = _resolve(args)
    result = api_request(url, token, "/api/fs/get", {"path": args.path})
    _output(args, result)

def cmd_mkdir(args):
    url, token = _resolve(args)
    result = api_request(url, token, "/api/fs/mkdir", {"path": args.path})
    _output(args, result)

def cmd_rename(args):
    url, token = _resolve(args)
    result = api_request(url, token, "/api/fs/rename", {
        "path": args.path, "name": args.new_name
    })
    _output(args, result)

def cmd_move(args):
    url, token = _resolve(args)
    src_dir = os.path.dirname(args.path) or "/"
    src_name = os.path.basename(args.path)
    dst_dir = args.dst.rstrip("/")
    # API expects: src_dir, dst_dir, names[]
    result = api_request(url, token, "/api/fs/move", {
        "src_dir": src_dir,
        "dst_dir": dst_dir,
        "names": [args.new_name] if args.new_name else [src_name]
    })
    _output(args, result)

def cmd_copy(args):
    url, token = _resolve(args)
    src_dir = os.path.dirname(args.path) or "/"
    src_name = os.path.basename(args.path)
    dst_dir = args.dst.rstrip("/")
    # API expects: src_dir, dst_dir, names[]
    result = api_request(url, token, "/api/fs/copy", {
        "src_dir": src_dir,
        "dst_dir": dst_dir,
        "names": [args.new_name] if args.new_name else [src_name]
    })
    _output(args, result)

def cmd_remove(args):
    url, token = _resolve(args)
    names = args.names if isinstance(args.names, list) else [args.names]
    result = api_request(url, token, "/api/fs/remove", {"names": names})
    _output(args, result)

def cmd_link(args):
    url, token = _resolve(args)
    result = api_request(url, token, "/api/fs/link", {
        "path": args.path,
        "method": args.method.upper()
    })
    _output(args, result)

# ─── Share Commands ────────────────────────────────────────────────────────────

def cmd_share_list(args):
    """List all shares created by current user."""
    url, token = _resolve(args)
    payload = {"page": args.page or 1, "per_page": args.per_page or 30}
    result = api_request(url, token, "/api/share/list", payload)
    # Add share links to each share
    if result.get("code") == 200:
        base_url = url.rstrip("/")
        for share in result.get("data", {}).get("content", []):
            if share.get("id"):
                share["share_link"] = f"{base_url}/@s/{share['id']}"
    _output(args, result)

def cmd_share_get(args):
    """Get share details by ID."""
    url, token = _resolve(args)
    # share-get uses query parameter, not POST body
    headers = {"Authorization": token, "Content-Type": "application/json"}
    resp = requests.get(
        f"{url}/api/share/get",
        params={"id": args.id},
        headers=headers,
        timeout=15
    )
    resp.encoding = "utf-8"
    try:
        result = resp.json()
    except Exception:
        result = {"code": 999, "message": f"Empty response: {resp.status_code}"}
    # Add share link to output
    if result.get("code") == 200 and result.get("data", {}).get("id"):
        share_id = result["data"]["id"]
        base_url = url.rstrip("/")
        result["data"]["share_link"] = f"{base_url}/@s/{share_id}"
    _output(args, result)

def cmd_share_create(args):
    """Create a new share for files/folders."""
    url, token = _resolve(args)
    # OpenList uses 'files' array, not 'path'
    files = [p.strip() for p in args.files.split(",")]
    payload: dict[str, object] = {"files": files}
    if args.password:
        payload["pwd"] = args.password
    if args.expire_hours:
        from datetime import datetime, timedelta, timezone
        expires = datetime.now(timezone(timedelta(hours=8))) + timedelta(hours=args.expire_hours)
        payload["expires"] = expires.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    result = api_request(url, token, "/api/share/create", payload)
    # Add share link to output
    if result.get("code") == 200 and result.get("data", {}).get("id"):
        share_id = result["data"]["id"]
        # Extract base URL (remove any path like /api, etc.)
        base_url = url.rstrip("/")
        result["data"]["share_link"] = f"{base_url}/@s/{share_id}"
    _output(args, result)

def cmd_share_update(args):
    """Update an existing share."""
    url, token = _resolve(args)
    payload = {"share_id": args.id}
    if args.password is not None:
        payload["password"] = args.password
    if args.expire_at is not None:
        payload["expire_at"] = args.expire_at
    result = api_request(url, token, "/api/share/update", payload)
    _output(args, result)

def cmd_share_delete(args):
    """Delete a share by ID."""
    url, token = _resolve(args)
    # Delete uses POST with query parameter
    result = api_request(url, token, "/api/share/delete", {}, query_params={"id": args.id})
    _output(args, result)

# ─── Index Commands ───────────────────────────────────────────────────────────

def cmd_index_build(args):
    """Build search index for all storages."""
    url, token = _resolve(args)
    result = api_request(url, token, "/api/admin/index/build", {})
    _output(args, result)

def cmd_index_update(args):
    """Update search index for specific paths."""
    url, token = _resolve(args)
    paths = [p.strip() for p in args.paths.split(",")] if args.paths else []
    result = api_request(url, token, "/api/admin/index/update", {"paths": paths})
    _output(args, result)

def cmd_index_clear(args):
    """Clear all search index data."""
    url, token = _resolve(args)
    result = api_request(url, token, "/api/admin/index/clear", {})
    _output(args, result)

def cmd_index_progress(args):
    """Check search index build progress."""
    url, token = _resolve(args)
    result = api_request(url, token, "/api/admin/index/progress", {}, method="GET")
    _output(args, result)

# ─── Batch Rename Commands ────────────────────────────────────────────────────

def cmd_batch_rename(args):
    """Batch rename multiple files in a directory."""
    url, token = _resolve(args)
    # Parse rename pairs: "old1:new1,old2:new2"
    rename_objects = []
    for pair in args.rename_pairs.split(","):
        pair = pair.strip()
        if ":" in pair:
            src, new = pair.split(":", 1)
            rename_objects.append({"src_name": src.strip(), "new_name": new.strip()})
    
    if not rename_objects:
        _output(args, {"code": 400, "message": "No valid rename pairs provided"})
        return
    
    result = api_request(url, token, "/api/fs/batch_rename", {
        "src_dir": args.src_dir,
        "rename_objects": rename_objects
    })
    _output(args, result)

def cmd_regex_rename(args):
    """Rename files using regular expression pattern."""
    url, token = _resolve(args)
    result = api_request(url, token, "/api/fs/regex_rename", {
        "src_dir": args.src_dir,
        "src_name_regex": args.src_regex,
        "new_name_regex": args.dst_regex
    })
    _output(args, result)

def cmd_upload(args):
    url, token = _resolve(args)
    if not os.path.isfile(args.file):
        print(json.dumps({"code": 400, "message": "File not found: " + args.file}))
        sys.exit(1)
    # file_path should be full path including filename
    file_path = args.path
    if not os.path.splitext(file_path)[1]:  # No extension, assume it's a directory
        filename = os.path.basename(args.file)
        file_path = file_path.rstrip("/") + "/" + filename
    result = api_upload(url, token, file_path, args.file,
                        as_task=args.async_upload, overwrite=args.replace)
    _output(args, result)

def cmd_search(args):
    """Smart search with fallback: API search -> traversal+filter."""
    url, token = _resolve(args)
    keyword = args.keyword.lower()
    path = args.path or "/"
    page = args.page or 1
    per_page = args.per_page or 50
    max_depth = args.max_depth if args.max_depth is not None else 6
    use_api = args.use_api

    results = []

    # Strategy 1: try API search first
    if use_api:
        api_result = api_request(url, token, "/api/fs/search", {
            "parent": path, "keywords": keyword, "page": page, "per_page": per_page
        })
        if api_result.get("code") == 200:
            items = api_result["data"]["content"]
            total = api_result["data"]["total"]

            # Check if keyword filtering actually works by comparing
            # the result count with a nonsense keyword.
            # If both return the same total, keyword filtering is broken.
            empty_result = api_request(url, token, "/api/fs/search", {
                "parent": path, "keywords": "___nonexistent___xyz", "page": 1, "per_page": 1
            })
            empty_total = empty_result.get("data", {}).get("total", 0)

            keyword_filtering_works = (total != empty_total or total < 50)

            if keyword_filtering_works:
                results = items
            else:
                # Keyword filtering is broken (allow_indexed=false).
                # Filter the API results client-side.
                matched = [i for i in items if keyword in i["name"].lower()]
                # If still too few results from API, fall back to traversal
                if len(matched) < 3:
                    results = _traverse_search(url, token, path, keyword, max_depth)
                else:
                    results = matched
        else:
            # API search failed, fall back to traversal
            results = _traverse_search(url, token, path, keyword, max_depth)
    else:
        results = _traverse_search(url, token, path, keyword, max_depth)

    # Paginate results
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = results[start:end]

    _output(args, {
        "code": 200,
        "message": "success",
        "data": {
            "content": page_items,
            "total": total,
            "page": page,
            "per_page": per_page
        }
    })

def _traverse_search(url, token, root_path, keyword, max_depth):
    """Recursively list directories to find files matching keyword."""
    results = []
    queue = [(root_path, 0)]
    visited = set()

    while queue and len(results) < 200:
        current_path, depth = queue.pop()
        if depth > max_depth:
            continue
        if current_path in visited:
            continue
        visited.add(current_path)

        try:
            resp = api_request(url, token, "/api/fs/list", {
                "path": current_path, "page": 1, "per_page": 200
            })
            if resp.get("code") != 200:
                continue
            items = resp.get("data", {}).get("content") or []
        except Exception:
            continue

        for item in items:
            name = item.get("name", "")
            full_path = (current_path.rstrip("/") + "/" + name).replace("//", "/")
            if keyword in name.lower():
                item["parent"] = current_path
                results.append(item)
            if item.get("is_dir") and depth < max_depth:
                queue.append((full_path, depth + 1))

    return results

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _resolve(args):
    cfg = load_config()
    url = (args.url or cfg.get("base_url", "")).rstrip("/")
    token = args.token or cfg.get("token", "")
    if not url:
        print(json.dumps({"code": 400, "message": "No OpenList URL. Use --url or config.json."}))
        sys.exit(1)
    return url, token

def _output(args, result):
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif args.quiet:
        if result.get("code") == 200:
            data = result.get("data", {})
            if isinstance(data, list):
                for item in data:
                    print(item.get("name", item))
            elif isinstance(data, dict):
                if "token" in data:
                    print(data["token"])
                elif "raw_url" in data or "proxy_url" in data:
                    print(data.get("proxy_url") or data.get("raw_url"))
                elif "content" in data:
                    for item in data["content"]:
                        print(item.get("name"))
                else:
                    print(json.dumps(data, ensure_ascii=False))
        else:
            print(result.get("message", result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="openlist.py",
        description="OpenList API command-line tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # login
    p = sub.add_parser("login", help="Login and save token")
    p.add_argument("--url", required=True, help="OpenList base URL")
    p.add_argument("--username", required=True)
    p.add_argument("--password", required=True)

    # list
    p = sub.add_parser("list", help="List directory")
    p.add_argument("--path", default="/")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--per-page", type=int, default=50)
    p.add_argument("--refresh", action="store_true")

    # get
    p = sub.add_parser("get", help="Get file/dir info")
    p.add_argument("--path", required=True)

    # mkdir
    p = sub.add_parser("mkdir", help="Create directory")
    p.add_argument("--path", required=True)

    # rename
    p = sub.add_parser("rename", help="Rename file/dir")
    p.add_argument("--path", required=True)
    p.add_argument("--new-name", required=True)

    # move
    p = sub.add_parser("move", help="Move file/dir")
    p.add_argument("--path", required=True)
    p.add_argument("--dst", required=True)
    p.add_argument("--new-name")

    # copy
    p = sub.add_parser("copy", help="Copy file/dir")
    p.add_argument("--path", required=True)
    p.add_argument("--dst", required=True)
    p.add_argument("--new-name")

    # remove
    p = sub.add_parser("remove", help="Delete file(s)/dir(s)")
    p.add_argument("--names", required=True,
                   help="Full path(s), comma-separated")

    # search
    p = sub.add_parser("search", help="Search files (auto-fallback to traversal)")
    p.add_argument("--path", default="/")
    p.add_argument("--keyword", required=True)
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--per-page", type=int, default=50)
    p.add_argument("--max-depth", type=int, default=6,
                   help="Max directory traversal depth (default 6)")
    p.add_argument("--no-api", dest="use_api", action="store_false", default=True,
                   help="Skip API search, use directory traversal directly")

    # link
    p = sub.add_parser("link", help="Get download link")
    p.add_argument("--path", required=True)
    p.add_argument("--method", default="GET")

    # upload
    p = sub.add_parser("upload", help="Upload file")
    p.add_argument("--path", required=True, help="Destination path on OpenList")
    p.add_argument("--file", required=True, help="Local file path")
    p.add_argument("--replace", action="store_true", help="Overwrite if exists")
    p.add_argument("--async-upload", action="store_true", help="Upload as async task")

    # share-list
    p = sub.add_parser("share-list", help="List all shares")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--per-page", type=int, default=30)

    # share-get
    p = sub.add_parser("share-get", help="Get share by ID")
    p.add_argument("--id", required=True, help="Share ID")

    # share-create
    p = sub.add_parser("share-create", help="Create a share")
    p.add_argument("--files", required=True, help="File/folder paths, comma-separated")
    p.add_argument("--password", help="Optional password protection")
    p.add_argument("--expire-hours", type=int, help="Expiration in hours from now")

    # share-update
    p = sub.add_parser("share-update", help="Update a share")
    p.add_argument("--id", required=True, help="Share ID")
    p.add_argument("--password", help="New password")
    p.add_argument("--expire-at", help="New expiration datetime")

    # share-delete
    p = sub.add_parser("share-delete", help="Delete a share")
    p.add_argument("--id", required=True, help="Share ID")

    # index-build
    p = sub.add_parser("index-build", help="Build search index (Admin)")
    p.add_argument("--async", dest="async_build", action="store_true",
                   help="Build index asynchronously")

    # index-update
    p = sub.add_parser("index-update", help="Update search index for paths (Admin)")
    p.add_argument("--paths", help="Paths to update, comma-separated (empty = all)")

    # index-clear
    p = sub.add_parser("index-clear", help="Clear all search index data (Admin)")

    # index-progress
    p = sub.add_parser("index-progress", help="Check search index build progress")

    # batch-rename
    p = sub.add_parser("batch-rename", help="Batch rename multiple files")
    p.add_argument("--src-dir", required=True, help="Source directory")
    p.add_argument("--rename-pairs", required=True,
                   help="Rename pairs, format: 'old1:new1,old2:new2'")

    # regex-rename
    p = sub.add_parser("regex-rename", help="Rename files using regex pattern")
    p.add_argument("--src-dir", required=True, help="Source directory")
    p.add_argument("--src-regex", required=True, help="Source name regex pattern")
    p.add_argument("--dst-regex", required=True, help="Replacement pattern")

    # Global args
    global_args = ["--token", "--json", "--quiet"]
    for name, p_obj in sub.choices.items():
        if name != "login":
            p_obj.add_argument("--url")
        for arg in global_args:
            if arg in ("--json", "--quiet"):
                p_obj.add_argument(arg, action="store_true")
            else:
                p_obj.add_argument(arg)

    args = parser.parse_args()

    CMD_MAP = {
        "login": cmd_login, "list": cmd_list, "get": cmd_get,
        "mkdir": cmd_mkdir, "rename": cmd_rename, "move": cmd_move,
        "copy": cmd_copy, "remove": cmd_remove, "search": cmd_search,
        "link": cmd_link, "upload": cmd_upload,
        "share-list": cmd_share_list, "share-get": cmd_share_get,
        "share-create": cmd_share_create, "share-update": cmd_share_update,
        "share-delete": cmd_share_delete,
        "index-build": cmd_index_build, "index-update": cmd_index_update,
        "index-clear": cmd_index_clear, "index-progress": cmd_index_progress,
        "batch-rename": cmd_batch_rename, "regex-rename": cmd_regex_rename
    }
    CMD_MAP[args.cmd](args)

if __name__ == "__main__":
    main()
