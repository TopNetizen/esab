"""命令行入口。stdio 为默认传输；HTTP 只在显式打开时监听，并且必须带令牌。"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.stdio import stdio_server

from esab import __version__
from esab.config import load_config
from esab.server import build_server
from esab.skill_vault import read_skill_tree, dump_public_json, write_skill

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


class StaticTokenVerifier:
    def __init__(self, token: str) -> None:
        self._token = token

    async def verify_token(self, token: str) -> AccessToken | None:
        if not self._token or not token:
            return None
        if len(token) != len(self._token):
            return None
        mismatch = 0
        for left, right in zip(token, self._token):
            mismatch |= ord(left) ^ ord(right)
        if mismatch != 0:
            return None
        return AccessToken(token=token, client_id="local-bridge", scopes=["bridge"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="esab", description="工程软件 MCP 标准客户端桥接器")
    parser.add_argument("--version", action="version", version=f"esab {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    stdio = sub.add_parser("stdio", help="通过标准输入输出提供 MCP")
    stdio.add_argument("--config", required=True, help="上游配置 JSON")

    http = sub.add_parser("http", help="在本机提供带令牌的 Streamable HTTP MCP")
    http.add_argument("--config", required=True)
    http.add_argument("--host", default="127.0.0.1")
    http.add_argument("--port", type=int, default=47331)
    http.add_argument("--token", default="", help="也可改用环境变量 ESAB_TOKEN")
    http.add_argument("--allow-remote", action="store_true", help="允许绑定非回环地址。默认拒绝。")

    agent = sub.add_parser("agent", help="启动工程软件操作运行时（stdio MCP）")
    agent.add_argument("--skills-root", default="", help="技能目录")

    decode = sub.add_parser("list-skills", help="扫描技能目录并输出明文索引")
    decode.add_argument("--skills-root", required=True)
    decode.add_argument("--out", required=True, help="技能输出目录。")
    return parser


def _reject_remote(host: str, allow_remote: bool) -> None:
    if host not in LOCAL_HOSTS and not allow_remote:
        raise SystemExit(f"拒绝绑定 {host}。HTTP 默认只监听回环地址；远程绑定需要同时传入 --allow-remote。")


async def _serve_runtime(server: object) -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())  # type: ignore[attr-defined]


async def _serve_stdio(config_path: str) -> None:
    specs = load_config(config_path)
    server = build_server(specs)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def serve_http(config_path: str, host: str, port: int, token: str) -> None:
    import uvicorn

    specs = load_config(config_path)
    server = build_server(specs)
    app = server.streamable_http_app(
        host=host,
        auth=AuthSettings(
            issuer_url=f"http://{host}:{port}",
            resource_server_url=f"http://{host}:{port}",
            validate_token_resource=False,
            required_scopes=["bridge"],
        ),
        token_verifier=StaticTokenVerifier(token),
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "agent":
        import os

        if args.skills_root:
            os.environ["ESAB_SKILLS_ROOT"] = args.skills_root
        from esab.runtime.host import build_agent_server

        server = build_agent_server()
        asyncio.run(_serve_runtime(server))
        return 0
    if args.command == "stdio":
        asyncio.run(_serve_stdio(args.config))
        return 0
    if args.command == "http":
        import os

        token = args.token or os.environ.get("ESAB_TOKEN", "")
        if not token:
            print("HTTP 模式必须提供 --token 或环境变量 ESAB_TOKEN。", file=sys.stderr)
            return 2
        _reject_remote(args.host, args.allow_remote)
        serve_http(args.config, args.host, args.port, token)
        return 0
    if args.command == "list-skills":
        from pathlib import Path

        loaded = read_skill_tree(Path(args.skills_root))
        write_skill(loaded, Path(args.out))
        print(dump_public_json(loaded), end="")
        return 0
    parser.error(f"未知命令 {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
