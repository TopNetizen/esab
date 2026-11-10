---
name: daylight-tools
description: 采光设计及计算分析工具集。当用户请求设置内饰面材料、窗体材料、污染程度、房间类型、采光计算配置、采光计算、一键计算、相机设置、眩光计算、查询/查看计算结果、生成/查看报告书时触发此技能。涵盖采光设计全流程的参数设置、计算分析、报告书生成等功能。
---

# 采光设计及计算工具集 (Daylight Tools)

本技能提供建筑采光设计及计算的全流程操作能力，包括房间类型设置、内饰面设置、窗体设置、污染程度设置、计算参数配置、计算执行、结果查询、报告生成与查看等功能。MCP 调用规范详见主技能 `SKILL.md`。

**采光设计的常规流程为：**
1. 房间类型设置；
2. 建筑材料设置，包括：内饰面材料设置、窗体材料设置、污染程度设置等；
3. 计算参数配置：设置计算范围、计算方法、统计方法、模拟计算时需要考虑的构件、天空模型等各种专业参数；
4. 采光计算；
5. 查看计算结果；
6. 生成报告书。

### 特别说明
1. 以"McpCommand"开头的工具，是需要用户和软件进行交互的，如果存在其他接口可以实现该功能，尽量避免使用这些接口。如果使用了这些接口，大概率需要等待用户手动和软件交互之后才能继续后续操作。
2. 以"McpCommand"开头的工具，均不需要入参，返回都是1000，不同的接口根据功能不同会有不同的msg。
3. **不支持**定时计算。
4. 一键计算功能仅支持进行采光计算。`GpDlAutoDaylightCalc`、`GpDlAutoDaylightCalc_Formula`、`GpDlAutoDaylightCalc_Simulate` 三个一键计算工具的差异详见指令映射表及共用接口文档。方案阶段优先使用`GpDlAutoDaylightCalc_Formula`。
5. 回复用户时，**禁止**直接展示工具名称、传给工具的参数和工具返回的错误代码，而要将其转换成中文进行回复。
6. 《绿色建筑评价标准》GB/T 50378-2019中取消了视野分析的条文，所以，当前Agent暂不支持视野分析功能。用户可手动操作软件进行相关计算与分析。

---

## 指令映射表

`command` 参数允许的值及其对应的功能说明如下：

### 标准选择
| Command Value | 功能描述 |
| :--- | :--- |
| `McpCommandGpDlSelCriteria` | 打开标准选择对话框。该对话框为模态对话框，关闭后该工具才会结束 |

### 房间类型设置
| Command Value | 功能描述 |
| :--- | :--- |
| `McpCommandGpDlRoomsMap` | 打开房间类型设置的右边面板。通过该面板，用户可以将房间设置为采光标准中的房间类型 |
| `McpCommandGpDlSetRoomType` | 在软件中选择房间设置其房间类型（用户交互设置后，该工具才会结束） |
| `GpDlGetAllRoomTypes` | 查询当前建筑中某模块下的所有房间类型，接口说明详见references/GpDlGetAllRoomTypes.md |
| `GpDlRoomTypeAutoMatch` | **房间类型智能匹配**：根据其他模块已设置的房间类型（如有，否则使用房间名称）自动匹配房间类型，匹配完成后返回所有房间类型的分配情况，接口说明详见references/GpDlRoomTypeAutoMatch.md |

### 内饰面设置
| Command Value | 功能描述 |
| :--- | :--- |
| `McpCommandGpDlInnerMatSet` | 打开内饰面设置的右边面板。通过该面板，用户可以设置墙、顶棚、地板等构件的内饰面材料 |
| `GpDlGetInnerFaceMaterialLibrary` | 查询所有可用的内饰面材料库，接口说明详见references/GpDlGetInnerFaceMaterialLibrary.md |
| `GpDlAddCustomInnerFaceMaterial` | 添加自定义内饰面材料，接口说明详见references/GpDlAddCustomInnerFaceMaterial.md |
| `GpDlSetInnerFaceMaterial` | 设置内饰面材料，接口说明详见references/GpDlSetInnerFaceMaterial.md |
| `GpDlGetDefaultInnerFaceMaterial` | 查询构件默认的内饰面材料，接口说明详见references/GpDlGetDefaultInnerFaceMaterial.md |
| `GpDlGetInnerFaceMaterialByName` | 根据名称查询内饰面材料全部信息，接口说明详见references/GpDlGetInnerFaceMaterialByName.md |

### 窗体设置
| Command Value | 功能描述 |
| :--- | :--- |
| `McpCommandGpDlWinMatSet` | 打开窗体材料设置的右边面板。通过该面板，用户可以设置窗、玻璃幕墙、门的透明部分等窗体的材料 |
| `GpDlGetWindowMaterialLibrary` | 查询所有可用的窗体材料库，接口说明详见references/GpDlGetWindowMaterialLibrary.md |
| `GpDlGetWindowMaterialByName` | 从窗体材料库中查询某个窗体材料（根据窗框名称和玻璃材料名称），接口说明详见references/GpDlGetWindowMaterialByName.md |
| `GpDlSetWindowMaterial` | 设置窗体材料，接口说明详见references/GpDlSetWindowMaterial.md |
| `GpDlGetWindowMaterial` | 查询窗体的材料设置，接口说明详见references/GpDlGetWindowMaterial.md |

### 污染程度设置
| Command Value | 功能描述 |
| :--- | :--- |
| `McpCommandGpDlPollutionSet` | 打开污染程度设置的右边面板。通过该面板，用户可以设置窗、玻璃幕墙、门的透明部分等窗体的污染程度 |

### 采光计算配置
| Command Value | 功能描述 |
| :--- | :--- |
| `GpDlSetDaylightCalcConfig` | 设置采光计算配置，接口说明详见references/GpDlSetDaylightCalcConfig.md |
| `GpDlGetDaylightCalcConfig` | 查询采光计算配置，接口说明详见references/GpDlGetDaylightCalcConfig.md |
| `McpCommandGpDlCalcAnaConfig_CG` | 打开采光计算配置对话框。该对话框为模态对话框，关闭后该工具才会结束 |

### 采光计算执行
| Command Value | 功能描述 |
| :--- | :--- |
| `GpDlExecuteDaylightCalc` | 根据项目当前配置，执行采光/眩光/人工照明计算，接口说明详见references/GpDlExecuteDaylightCalc.md |
| `GpDlAutoDaylightCalc` | **一键计算（默认）**：根据项目当前配置进行采光计算，不修改计算方法设置。如果当前项目没有设置计算范围，会默认设置为全楼计算。接口说明详见references/GpDlAutoDaylightCalc.md（三个一键计算工具共用此文档） |
| `GpDlAutoDaylightCalc_Formula` | **公式法一键计算**：自动设置为仅公式法进行**快速**采光计算，适用于**方案阶段**。接口说明见references/GpDlAutoDaylightCalc.md（共用文档） |
| `GpDlAutoDaylightCalc_Simulate` | **模拟法一键计算**：自动设置为模拟法进行采光计算，并按照绿建统计法进行统计分析，适用于**详细**采光分析。接口说明见references/GpDlAutoDaylightCalc.md（共用文档） |

| `McpCommandGpDlMultipleScheme` | 打开多方案设计分析对话框 |

### 眩光相关配置
| Command Value | 功能描述 |
| :--- | :--- |
| `McpCommandGpDlCameraSet` | 打开相机设置的右边面板。通过该面板，用户可以设置观察相机，用于眩光计算 |
| `McpCommandGpDlButtonCamera` | 在软件中以交互方式设置相机（需要用户手动操作软件界面，除非用户主动要求，否则尽量使用`McpCommandGpDlCameraSet`） |
| `McpCommandGpDlCalcAnaConfig_XG` | 打开眩光计算分析配置对话框 |

### 眩光计算执行
| Command Value | 功能描述 |
| :--- | :--- |
| `GpDlExecuteDaylightCalc` | 执行眩光计算（calcType=glare），接口说明详见references/GpDlExecuteDaylightCalc.md |

### 结果分析查看
| Command Value | 功能描述 |
| :--- | :--- |
| `GpDlGetCalcResult` | 查询当前建筑采光计算结果，接口说明详见references/GpDlGetCalcResult.md |
| `McpCommandGpDlResultAnalyse` | 打开结果分析对话框（全面展示结果分析情况。该对话框是模态对话框，关闭后该工具才会结束） |
| `McpCommandGpDlDisplayIlluminance` | 在图纸上显示照度（采光计算后才会有值） |
| `McpCommandGpDlDisplayCav` | 在图纸上显示采光系数（采光计算后才会有值） |
| `McpCommandGpDlDisplayCavDB` | 在图纸上显示采光达标情况（采光计算后才会有值） |
| `McpCommandGpDlDisplayCavInterior` | 在图纸上显示内区采光系数（采光计算后才会有值） |
| `McpCommandGpDlDisplayCavInteriorDB` | 在图纸上显示内区采光达标情况（采光计算后才会有值） |
| `McpCommandGpDlDisplayDgi` | 在图纸上显示眩光指数（眩光计算后才会有值） |
| `McpCommandGpDlShowRoomResult` | 在对话框中显示图纸上选中的功能房间的动态采光结果 |
| `McpCommandGpDlAnnualExport` | 导出年度动态采光结果 |

**特别说明：**
1. 在图纸上显示照度、采光系数、采光系数达标情况、内区采光系数、内区采光达标情况、眩光指数等内容是互斥的，仅能展示最后一个命令执行效果。比如，先执行了McpCommandGpDlDisplayCav，又执行了McpCommandGpDlDisplayCavInterior，那么，图纸上将仅展示后一个命令执行的效果，也就是展示内区采光系数。
2. 标准层中看不到以上各种指标，需切换到普通层才能看到。通过GetCurrentModelView命令可以查看当前处于哪个视图，详见`../context-tools/references/get-current-model-view.md`。


### 报告书
| Command Value | 功能描述 |
| :--- | :--- |
| `GpDlCreateReport` | 生成采光及眩光计算分析报告书，执行后不弹窗阻塞进程，返回生成的报告书路径，接口说明详见references/GpDlCreateReport.md |
| `McpCommandGpDlShowReport` | 打开采光及眩光计算分析报告书 |

---

## 调用示例

### 示例 1：执行采光计算
用户请求："对当前项目进行采光模拟分析。"

**Agent 构建的参数：**

```json
{
  "command": "GpDlAutoDaylightCalc",
  "parameters": {}
}
```

### 示例 2：设置内饰面材质
用户请求："我要设置内饰面材料。"

**Agent 构建的参数：**
```json
{
  "command": "GpDlSetInnerFaceMaterial",
  "parameters": {
    "scope": {
      "type": "wholeBuild"
    },
    "components": [
      {
        "componentType": "wall",
        "material": {
          "source": "《建筑采光设计标准》GB 5033-2013",
          "name": "白色乳胶漆",
          "reflectance": 0.84
        }
      }
    ]
  }
}
```

### 示例 3：公式法快速计算
用户请求："方案阶段，快速算一下采光看是否达标。"

**Agent 构建的参数：**

```json
{
  "command": "GpDlAutoDaylightCalc_Formula",
  "parameters": {}
}
```

### 示例 4：生成报告
用户请求："生成一份采光分析报告。"

**Agent 构建的参数：**

```json
{
  "command": "GpDlCreateReport",
  "parameters": {}
}
```
