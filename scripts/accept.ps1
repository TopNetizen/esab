# 验收。默认只跑模拟夹具，不连接真实软件。
# -EnumerateUrl 只列出已经在监听的 MCP，不调用工具。
param(
  [string]$EnumerateUrl
)

$ErrorActionPreference = "Stop"
$python = (Get-Command python).Source

if ($EnumerateUrl) {
  Write-Output "只读枚举。不会调用工具。"
  & $python -m esab.acceptance --enumerate $EnumerateUrl
  exit $LASTEXITCODE
}

Write-Output "运行模拟夹具验收。"
& $python -m esab.acceptance
exit $LASTEXITCODE
