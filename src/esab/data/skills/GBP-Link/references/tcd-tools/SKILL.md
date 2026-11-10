---
name: tcd-tools
description: 仅当用户意图为【室内热舒适】时触发：支持一键计算和报告书生成。关键词：一键计算、报告书生成。
---

# TCD 模块

本技能用于室内热舒适的计算和报告书的生成。MCP 调用规范详见主技能 `SKILL.md`。

## 工具目录

### ExecuteTCDCalc — 一键计算

**工具说明**：执行室内热舒适一键计算。执行前必须已加载 bdls，且项目中存在单体。执行完成后通过返回的结论列表反馈计算结果。

**请求实例**：
```json
{
  "command": "ExecuteTCDCalc",
  "parameters": {}
}
```

**返回结果**：
```json
{
  "code": 1000,
  "msg": "一键计算完成。",
  "result": {
    "conclusion": [
      "结论1xxx",
	  "结论2xxx"
    ]
  }
}
```

| 返回字段 | 类型 | 说明 |
|----------|------|------|
| code | int | 状态码（1000 成功） |
| msg | string | 提示信息 |
| result.conclusion | array | 生成的结论列表（string 数组），可直接展示给用户 |

### CreateTCDReport — 报告书生成

**工具说明**：生成室内热舒适计算报告书，并返回生成的报告书文件路径，不会打开报告书。

**请求实例**：
```json
{
  "command": "CreateTCDReport",
  "parameters": {}
}
```

**返回结果**：
```json
{
  "code": 1000,
  "msg": "生成报告书成功。",
  "result": {
    "path": "[bdls所在路径]\\[bdls文件名称]-节能及绿建报告书汇总\\[项目名称]_室内热舒适评价分析报告.doc"
  }
}
```

| 返回字段 | 类型 | 说明 |
|----------|------|------|
| code | int | 状态码（1000 成功） |
| msg | string | 提示信息 |
| result.path | string | 生成的报告书文件路径 |
