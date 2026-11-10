"""Struct Bridge 自写 Abaqus 桥接插件。

本文件是一个 Abaqus/CAE 启动插件。用户把它放到 Abaqus 的 plugins 目录：
    Windows: C:\\Users\\<user>\\Documents\\AbaqusPlugins\\struct_abaqus_bridge.py

CAE 启动时会 import 本文件并调用 `def __init__()`（Abaqus plugin 约定）。
插件在后台线程监听 127.0.0.1:48152，按换行分隔 JSON 协议接受代码执行请求。

协议（与 bridge_client.py 完全对应）：
    请求: {"id": "...", "method": "ping|health|execute", "params": {...}}
    响应: {"id": "...", "ok": true, "result": {...}}
          {"id": "...", "ok": false, "error": {"message": "..."}}

execute params:
    code:       要在 Abaqus Python 环境中 exec 的代码
    work_dir:   可选，切换 cwd
    response_mode: "normal" | "quiet"
    timeout:    秒（本插件不强制杀——Abaqus 脚本不能从外部中断）

本插件不含任何专有代码。它只是一个标准的 Abaqus startup script，
用 socket 把外部 Python 发来的代码在 Abaqus 内 exec。
"""

import json
import os
import socket
import sys
import threading
import traceback

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 48152
MAX_BYTES = 16 * 1024 * 1024

_server_socket = None
_server_thread = None
_running = False


def _handle_client(conn, addr):
    """处理一个客户端连接：读一行 JSON，执行，返回一行 JSON。"""
    try:
        conn.settimeout(300.0)
        buffer = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                return
            buffer += chunk
            if b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                try:
                    req = json.loads(line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    _send(conn, {"id": None, "ok": False, "error": {"message": f"bad json: {exc}"}})
                    continue

                method = req.get("method", "")
                req_id = req.get("id")
                params = req.get("params") or {}

                if method == "ping":
                    _send(conn, {"id": req_id, "ok": True, "result": {"pong": True}})
                elif method == "health":
                    _send(conn, {
                        "id": req_id,
                        "ok": True,
                        "result": {
                            "status": "ok",
                            "plugin": "esab-abaqus",
                            "version": "0.4.0",
                            "pid": os.getpid(),
                        },
                    })
                elif method == "execute":
                    code = params.get("code", "")
                    work_dir = params.get("work_dir")
                    _execute(conn, req_id, code, work_dir)
                else:
                    _send(conn, {
                        "id": req_id,
                        "ok": False,
                        "error": {"message": f"unknown method: {method}"},
                    })
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _send(conn, obj):
    data = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
    conn.sendall(data + b"\n")


def _execute(conn, req_id, code, work_dir):
    """在 Abaqus Python 环境中执行代码。"""
    import io
    from contextlib import redirect_stdout, redirect_stderr

    old_cwd = os.getcwd()
    if work_dir:
        try:
            os.chdir(work_dir)
        except OSError:
            pass

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    result_value = None
    error = None

    try:
        # Abaqus 内建 mdb/session 由 CAE 提供
        globals_dict = {"__name__": "__abaqus_exec__"}
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = stdout_buf
        sys.stderr = stderr_buf
        try:
            compiled = compile(code, "<abaqus_exec>", "exec")
            exec(compiled, globals_dict)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    except Exception:
        error = traceback.format_exc()

    os.chdir(old_cwd)

    if error:
        _send(conn, {
            "id": req_id,
            "ok": False,
            "error": {"message": error},
            "result": {
                "stdout": stdout_buf.getvalue(),
                "stderr": stderr_buf.getvalue(),
            },
        })
    else:
        _send(conn, {
            "id": req_id,
            "ok": True,
            "result": {
                "stdout": stdout_buf.getvalue(),
                "stderr": stderr_buf.getvalue(),
            },
        })


def _server_loop():
    global _running
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((DEFAULT_HOST, DEFAULT_PORT))
    except OSError:
        # 端口被占（可能是已运行的 Agent 插件），不报错，静默退出
        return
    srv.listen(8)
    srv.settimeout(1.0)
    _running = True

    while _running:
        try:
            conn, addr = srv.accept()
        except socket.timeout:
            continue
        except OSError:
            break
        t = threading.Thread(target=_handle_client, args=(conn, addr), daemon=True)
        t.start()

    try:
        srv.close()
    except Exception:
        pass


def __init__():
    """Abaqus plugin 入口：CAE 启动时调用。"""
    global _server_thread
    if _server_thread is None:
        _server_thread = threading.Thread(target=_server_loop, daemon=True)
        _server_thread.start()
