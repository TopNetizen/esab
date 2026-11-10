# 安装工程软件操作运行时。不修改任何软件的许可。
param(
  [string]$Wheel = ""
)
$ErrorActionPreference = "Stop"
$python = (Get-Command python).Source
& $python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { Write-Output "需要 Python 3.11 或以上。"; exit 2 }
if ($Wheel) {
  & $python -m pip install $Wheel
} else {
  & $python -m pip install "esab[win32]"
}
Write-Output "安装完成。本安装不会打开软件，也不会绕过授权。"
