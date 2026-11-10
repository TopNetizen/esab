# 逐软件只读诊断。不创建模型，不启动计算。
$ErrorActionPreference = "Stop"
$python = (Get-Command python).Source
& $python -m esab.software_report
exit $LASTEXITCODE
