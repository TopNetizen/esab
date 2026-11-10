---
name: cs-tools
description: >-
  仅当用户意图为【方案碳】时触发：支持方案碳的设置、计算，及报告书的生成。关键词：读取、添加建筑信息、计算、查看结果、报告书路径。
---

# CS 模块（方案碳）

本技能用于方案碳的设置与计算。MCP 调用规范详见主技能 `SKILL.md`。

## 工具目录

### LoadCurrentBuilding — 加载当前建筑

**说明**：必须加载了bdls，且有单体。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `years` | int | 是 | 设计使用年限（年） |
| `totalArea` | double | 是 | 总的用地面积（㎡） |
| `greeningRate` | double | 是 | 绿化率（%） |
| `considerArea` | int | 是 | 0 地上面积+地下；1地上面积 |

**示例**：
```json
{"years": 60, "totalArea": 50000, "greeningRate": 48, "considerArea":1}
```

**成功返回**：`{"buildType": "建筑1","buildType": "公共建筑","buildHeight" : 18.0, "upFloors" : 1,"downFloors" : 0, "upArea" : 100.0,"downArea" : 0}`

### AddNewBuilding — 添加一条建筑信息

**说明**：无。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `buildName` | string | 是 | 建筑名称 |
| `buildType` | string | 是 | 建筑类型：居住建筑 公共建筑 商住两用 工业建筑 |
| `construct` | string | 否 | 结构类型：混凝土结构，剪力墙结构 ，钢结构 ，木结构，合结构-以钢结构为主，混合结构-以木结构为主 |
| `decorate` | string | 否 | 装修情况：精装修,毛坯，粗装修 |
| `buildHeight` | double | 是 | 建筑高度 |
| `upFloors` | int | 是 | 地上层数 |
| `downFloors` | double | 是 | 地下层数 |
| `upArea` | double | 是 | 建筑的地上面积（㎡） |
| `downArea` | double | 是 | 建筑的地下面积（㎡） |
| `years` | int | 是 | 设计使用年限（年） |
| `totalArea` | double | 是 | 总的用地面积（㎡） |
| `greeningRate` | double | 是 | 绿化率（%） |
| `considerArea` | int | 是 | 0 地上面积+地下；1地上面积 |

**示例**：
```json
{ "buildName": "建筑1", "buildType" : "公共建筑","construct" : "混凝土结构","decorate" : "精装修", "buildHeight" : 18.0, "upFloors" : 1,
"downFloors" : 0, "upArea" : 100.0, "downArea" : 0, "years": 60, "totalArea": 50000, "greeningRate": 48, "considerArea":1}
```

**成功返回**：`{}`

### CalcateCarbonAndGetResult — 计算建筑的碳排放，然后查看结果，并返回生成的方案碳排放报告书的路径

**说明**：无。

无参数

**成功返回**：`{"produceCarbon" : 18.0, "recyclingCarbon" : 1,"constructCarbon" : 0, "runCarbon" : 100.0,"deMolishCarbon" : 0,
"liftCarbon" : 0, "runCarbon" : 100.0,"everyAreaCarbon" : 0,"everyAreaEveryYearRunCarbon" : 0, "greenCarbon" : 100.0}`

> 返回信息中,`produceCarbon`生产运输阶段碳排放量（tCO2）,`recyclingCarbon`回收阶段减碳量（tCO2）,`constructCarbon`建造阶段碳排放量（tCO2）,`runCarbon`运行阶段碳排放量（tCO2）,`deMolishCarbon`拆除阶段碳排放量（tCO2）,
`liftCarbon`全生命周期碳排放量（tCO2）,`everyAreaCarbon`单位面积全生命周期碳排放量（tCO2e/㎡）,`everyAreaEveryYearRunCarbon`单位面积年运行碳排放量（[tCO2/(㎡*a)]）,`greenCarbon`绿化碳汇减碳量（tCO2）,

### GetReporPathCS — 生成方案碳排放报告书

**说明**：生成方案碳排放报告书，返回报告书所在路径

无参数

**成功返回**：`{"GetReporPathCS" :"" }`
