# 在已安装目标工程软件的 Windows 主机上做只读诊断。
# 不启动软件，不调用工具，不打印授权 token。

param(
    [string]$AgentHome = "",
    [string]$EnumerateUrl = "",
    [int]$ProcessId = 0
)

$ErrorActionPreference = "Stop"

$python = (Get-Command python).Source
Write-Output "=== esab 诊断 ==="
Write-Output "python: $python"

if ($ProcessId -gt 0) {
    Write-Output "`n--- 端口发现 (PID $ProcessId) ---"
    & $python -c "from esab.adapters.port_discovery import discover_mcp_url; print(discover_mcp_url($ProcessId))"
}

if ($EnumerateUrl) {
    Write-Output "`n--- 枚举 $EnumerateUrl ---"
    & $python -m esab.acceptance --enumerate $EnumerateUrl
}

Write-Output "`n诊断完成。没有启动任何工程软件，也没有调用建模或计算工具。"
