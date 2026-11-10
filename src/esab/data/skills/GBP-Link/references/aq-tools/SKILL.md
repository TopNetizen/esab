---
name: aq-tools
description: >-
  仅当用户意图为【空气质量】时触发：支持空气质量的计算、设置。关键词：一键计算、房间类型、装修方案、污染物、控制措施、设置、分析结论、报告书。
---

# AQ 模块

本技能用于空气质量的设置与计算。MCP 调用规范详见主技能 `SKILL.md`。

## 工具目录

### GpAQOneClickCalculate — 一键计算

**说明**：必须加载了bdls，且有单体。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `isUseClear` | bool | 是 | 是否使用净化装置 |
| `isOptimize` | bool | 是 | 是否自动进行优化（不使用净化装置，且计算不得分，将添加净化装置计算），当不使用净化装置时弹出此条参数 |

**示例**：
```json
{"isUseClear": true, "isOptimize": true}
```

**成功返回**：`{}`

### GpAQGetRoomTypes — 查询当前建筑有哪些空气质量的房间类型

**说明**：必须加载了bdls，且有单体。只是关键字查询，此命令不展示给用户，无论如何也不展示（打死也不展示），只在污染物设置或控制措施才可调用

无参数

**成功返回**：`{"roomTypes" : ["卧室,卫生间,……"]}`

### GpAQGetSchemes — 查询软件中有哪些装修方案

**说明**：只是关键字查询，此命令不展示给用户，无论如何也不展示（打死也不展示），只在污染物设置或控制措施才可调用

无参数

**成功返回**：`{"schemes" :"办公方案一，办公方案二，……" }`

### GpAQSetPollutant — 污染物设置

**说明**：必须加载了bdls，且有单体。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `chemicalPollScheme` | string | 是 | 装修方案，装修方案可以填写无 |
| `areaType` | string | 是 | 应用于区域范围类型:building-整栋建筑，floor-按楼层 |
| `ids` | array | 是 | 楼层id，当应用于区域范围类型选择为building时，不展示此项，若选择为floor时，展示此项作为补充提问|
| `roomTypes` | array | 是 | 房间类型列表，可以多选 |

**示例**：
```json
{ "chemicalPollScheme":"办公方案一","areaType": "building","ids": ["109","110","111"], "roomTypes":["卧室","起居室"]}
```

**成功返回**：`{"roomCount":100}`

### GpAQSetControlMeasureSimple — 控制措施设置

**说明**：必须加载了bdls，且有单体。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `isOpenWindowVentilatePM` | bool | 是 | 颗粒物是否设置为开窗通风 |
| `isOpenWindowVentilateChem` | bool | 是 | 污染物是否设置为开窗通风 |
| `isHavePurify` | bool | 是 | 是否有净化装置 |
| `setNewWindWay` | int | 是 | 新风装置的设置方式：0-全新风空调系统,1-无新风空调系统，2-新风与回风混合系统 |
| `areaType` | string | 是 | 应用于区域范围类型:building-整栋建筑，floor-按楼层 |
| `ids` | array | 是 | 楼层id，当应用于区域范围类型选择为building时，不展示此项，若选择为floorg时，展示此项作为补充提问|
| `roomTypes` | array | 是 | 房间类型列表，可以多选 |

**示例**：
```json
{  "isOpenWindowVentilatePM" : true,"isOpenWindowVentilateChem" : true,"isHavePurify":true,"setNewWindWay":2,"areaType":"building","ids":[109, 110, 111],"roomTypes":["主卧卫生间","卧室","起居室"] }
```

**成功返回**：`{"roomCount":100}`

##  GpAQGetAnalysisConclusion — 查询当前建筑的空气质量分析结论

**说明**：必须加载了bdls，且有单体。若没有进行一键计算或者未设置主要功能房间，结论为空。成功返回的结论文本以\n分割。

无参数

**成功返回**：`{"analysisConclusion" : "5.1.2 室内空气污染物浓度限量符合规定：氡不大于150Bq/m3，甲醛不大于0.07mg/m3，氨不大于0.15mg/m3，苯不大于0.06mg/m3，甲苯不大于0.15mg/m3，二甲苯不大于0.20mg/m3，TVOC不大于0.45mg/m3。\n5.1.3 室内空气污染物浓度测量应符合下列规定：\n1  除氡外，污染物浓度测量值均应为室内测量值扣除室外上风向空气中污染物浓度测量值（本底值）后的测量值；\n2  污染物浓度测量值的极限值判定应采用全数值比较法。"}`

##  GpAQCreateReport — 生成报告书

**说明**：必须加载了bdls，且有单体，若没有进行一键计算或者未设置主要功能房间，报告书内容可能会有缺失，最好是在进行一键计算之后再生成报告书。返回的内容为生成的报告书所在的路径，用', '分割。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `isCreateAppendix` | bool | 是 | 是否生成报告书附录 |

**示例**：
```json
{"isCreateAppendix": true}
```

**成功返回**：`{}`
