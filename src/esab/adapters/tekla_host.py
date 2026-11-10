"""Tekla 连接。"""

from __future__ import annotations

from esab.adapters.common import ConnectResult

EVIDENCE = "vendored tekla.runtime：pythonnet 加载年度程序集，Model.GetConnectionStatus()"


def connect_tekla() -> ConnectResult:
    try:
        from esab.adapters.tekla import runtime as tekla_runtime
    except ImportError as exc:
        return ConnectResult(
            ok=False,
            software="Tekla",
            message=f"无法加载 Tekla 运行时：{exc}。请 pip install esab[tekla]。",
            evidence=EVIDENCE,
            entry="adapters.tekla_host.connect_tekla",
        )
    try:
        session = tekla_runtime.connect_tekla()
    except Exception as exc:
        return ConnectResult(
            ok=False,
            software="Tekla",
            message=f"{type(exc).__name__}: {exc}",
            evidence=EVIDENCE,
            entry="adapters.tekla_host.connect_tekla",
        )
    return ConnectResult(
        ok=True,
        software="Tekla",
        message=f"已连接正在运行的 Tekla {session.program_version}。",
        evidence=EVIDENCE,
        entry="adapters.tekla_host.connect_tekla",
        live_verified=True,
        injected=["tekla", "model"],
        details={"value": session, "bin": session.tekla_bin},
    )
