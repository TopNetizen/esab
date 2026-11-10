---
name: cfd-tools
description: 建筑室外风环境CFD模拟计算与分析工具集。当用户请求一键计算、获取计算状态、查看/获取统计分析判断结论、重新统计分析、生成/查看报告书时触发此技能。涵盖室外风环境模拟的全流程计算、分析判断、报告书生成与查看等功能。
---

# 建筑室外风环境 CFD 模拟计算与分析工具集 (CFD Tools)

本技能提供建筑室外风环境 CFD 模拟计算与分析的全流程操作能力，包括一键计算、工况计算状态查询、统计分析判断结论获取、重新统计、报告书生成与查看等功能。MCP 调用规范详见主技能 `SKILL.md`。

**室外风环境模拟分析的常规流程为：**
1. 创建工况（用户手动操作）；
2. 计算配置（用户手动操作）；
3. 一键计算（自动完成计算、统计、判断）；
4. 查看/获取计算状态；
5. 获取统计分析判断结论；
6. 生成报告书。

## 特别说明
1. 本模块**仅支持 OpenFOAM 计算内核**，Stream 内核已不再使用，对外不再开放。
2. 计算前需要确保已创建好工况。如果当前没有工况，相关工具会返回错误信息。
3. 一键计算会自动弹出 CAD 计算界面，用户可见计算过程，计算完成后自动关闭。
4. **不支持**定时计算或后台静默计算。
5. 回复用户时，**不要**直接展示传给工具的参数和工具返回的错误代码，而要将其转换成中文进行回复。
6. 分析判断结论基于用户当前选中的绿建标准。

---

## 指令映射表

`command` 参数允许的值及其对应的功能说明如下：

### 一键计算
| Command Value | 功能描述 |
| :--- | :--- |
| `CFDAutoCalc` | 执行一键计算（计算、统计、判断全流程），接口说明详见 references/CFDAutoCalc.md |

### 计算状态查询
| Command Value | 功能描述 |
| :--- | :--- |
| `CFDGetCalcStatus` | 获取所有工况的计算状态，接口说明详见 references/CFDGetCalcStatus.md |

### 结果分析判断
| Command Value | 功能描述 |
| :--- | :--- |
| `CFDGetResult` | 获取统计分析判断结论（包含每个工况的详细达标判断、季节性分组结论、评分和最终结论），接口说明详见 references/CFDGetResult.md |
| `CFDReStat` | 重新统计分析（包含重新生成图片），接口说明详见 references/CFDReStat.md |

### 报告书
| Command Value | 功能描述 |
| :--- | :--- |
| `CFDCreateReport` | 生成室外风环境 CFD 模拟计算分析报告书，接口说明详见 references/CFDCreateReport.md |
| `CFDShowReport` | 打开(查看)已生成的报告书，接口说明详见 references/CFDShowReport.md |
| `CFDGetReportPath` | 获取报告书路径（检查报告书文件是否存在），接口说明详见 references/CFDGetReportPath.md |

---

## 核心数据结构说明

### 季节枚举

| 枚举值 | 说明 |
|--------|------|
| `夏季` | 夏季工况 |
| `过渡季` | 过渡季节工况 |
| `冬季` | 冬季工况 |
| `春季` | 春季（拓展工况） |
| `秋季` | 秋季（拓展工况） |

### 风向枚举（16方位）

N（北）、NNE（北东北）、NE（东北）、ENE（东东北）、E（东）、ESE（东东南）、SE（东南）、SSE（南东南）、S（南）、SSW（南西南）、SW（西南）、WSW（西西南）、W（西）、WNW（西西北）、NW（西北）、NNW（北西北）

### 风速类型

| 类型 | 说明 |
|------|------|
| 季平均风速 | 整个季节的平均风速 |
| 主要方向季平均风速 | 整个季节中主要方向上的平均风速 |
| 季最大风速 | 整个季节的最大风速 |
| 主要方向季最大风速 | 整个季节中主要方向上的最大风速 |

---

## 调用示例

### 示例 1：一键计算

用户请求："**帮我执行室外风环境计算。**"

**Agent 构建的参数：**

```json
{
  "command": "CFDAutoCalc",
  "parameters": {}
}
```

如果所有工况都已计算过，会直接返回统计分析判断结论。如果需要强制重新计算，可增加参数：

```json
{
  "command": "CFDAutoCalc",
  "parameters": {
    "forceRecalc": true
  }
}
```

### 示例 2：查询计算状态

用户请求："**计算完成了没有？**"

**Agent 构建的参数：**

```json
{
  "command": "CFDGetCalcStatus",
  "parameters": {}
}
```

### 示例 3：获取分析结论

用户请求："**看看结果怎么样，达标了没有？**"

**Agent 构建的参数：**

```json
{
  "command": "CFDGetResult",
  "parameters": {}
}
```

### 示例 4：重新统计分析

用户请求："**重新统计分析一下结果。**"

**Agent 构建的参数：**

```json
{
  "command": "CFDReStat",
  "parameters": {}
}
```

### 示例 5：生成报告书

用户请求："**帮我生成一份风环境分析报告。**"

**Agent 构建的参数：**

```json
{
  "command": "CFDCreateReport",
  "parameters": {}
}
```

### 示例 6：获取报告书路径

用户请求："**报告书在哪？**"

**Agent 构建的参数：**

```json
{
  "command": "CFDGetReportPath",
  "parameters": {}
}
```

### 示例 7：打开报告书

用户请求："**帮我打开报告书。**"

**Agent 构建的参数：**

```json
{
  "command": "CFDShowReport",
  "parameters": {}
}
```
