---
name: load-forecast
description: >-
  通过 PKPM 负荷预测 HTTP 服务对建筑进行冷负荷/热负荷预测，返回典型气象年逐日或逐时负荷数据。当用户提到负荷预测、冷负荷、热负荷、冷热负荷预测、能耗预测等关键词时触发。
---

# 负荷预测

通过外部 HTTP 服务（非 MCP `galp_tool_invoke`）对建筑进行冷、热负荷预测，得到典型气象年逐日/逐时负荷数据及预测时使用的参数。服务文档见  。

## 与其它子技能的区别

本技能调用的是**外部 REST 接口**，不走 MCP 《gbpmcp》 服务，因此主技能 SKILL.md 中的 `galp_tool_invoke` 状态码 1000~1004 及「当前模型视图」等规则对本技能**不适用**。本技能只做一件事：根据用户给出的建筑信息，构造请求体并发起 HTTP 预测请求，最后把结果转成中文说明给用户。

## 调用规范

token 认证与请求地址已在 python 脚本 `references/load-forecast/scripts/load_forecast.py` 内部封装，agent 无需关心 URL、鉴权 Header 等细节，直接调用脚本即可。

### Query 参数（URL 后拼接）

| 参数 | 必填 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| load_type | 否 | string | 3 | 负荷类型：1-热负荷；2-冷负荷；3-冷负荷+热负荷 |
| output_type | 否 | string | 1 | 输出精度：1-逐日负荷；2-逐时负荷 |
| min_temp_startup_condition | 否 | string | 24 | 启动空调的最低温度（℃，默认 24，来源 GB19577-2024 附录A.2） |
| min_temp_startup_heating | 否 | string | -12 | 室外侧名义制热工况（℃，默认 -12，来源 GB21454-2021 附录A.1） |
| max_temp_startup_heating_residence | 否 | string | 15 | 户用建筑启动采暖最高温度（℃，默认 15，来源 GB21454-2021 附录A.1） |
| max_temp_startup_heating_industrial_commercial | 否 | string | 13 | 工商业建筑启动采暖最高温度（℃，默认 13，来源 GB21454-2021 附录A.1） |

### Body 请求体（JSON）

本技能提供**统一入口函数 `LoadForecast`**。用户只需给出关键输入，其余参数可由服务端内部补齐。

**必须/建议由用户提供的关键输入：**
- `buildingFunction`（建筑功能，必填，见下表取值）
- `cityId 或 cityName`（必填，用于关联气象数据）。**二者二选一、必传其一**；若两者均传，优先使用 `cityId`
- `buildingArea`（建筑面积，建议提供，㎡）

**字段取值约束：**
- `buildingFunction` 取值：住宅、集体宿舍、办公、医院（门诊）、学院、商场(店)或书店、旅店、体育馆、文化娱乐
- `systemTypeIDs` 可选值：1-两管制风机盘管加独立新风; 2-散热器供暖、风机盘管系统; 3-四管制风机盘管加独立新风; 4-房间空调器; 5-分体式空调; 6-多联机加独立新风; 7-热泵型新风一体机; 8-变风量系统（风机动力型）; 9-变风量系统（无风机型）; 10-定风量全空气系统; 11-单元式空调; 12-空系统。其中，适用于居建的暖通空调系统ID有：4 5 6 7 11 12；适用于公建的暖通空调系统ID有：1 2 3 6 7 8 9 10 11 12。
- `buildingDirection` 建筑朝向。输入值可以为以下三种之一：
  - `南北向` `东西向` 二者之一
  - 数值，表示坐标系正北向与指北针方向的逆时针夹角。比如：0表示正北向，45表示西北，90表示正西，依此类推；
  - 向量，表示指北针方向。比如：`(0,1)`表示正北向，`(-1,0)`表示正西向。

**Body参数列表**

| 字段 | 类型 | 说明 |
|------|------|------|
| buildingFunction | string | 建筑功能（**必填**，应由用户指定） |
| cityId | int | 城市ID。与 `cityName` 二选一、必传其一；若两者均传，优先使用 `cityId` |
| cityName | string | 城市名称。与 `cityId` 二选一、必传其一 |
| buildingDirection | string/number | 建筑朝向 |
| buildingFloorCount | int | 建筑总层数 |
| buildingOvergroundFloorCount | int | 地上层数 |
| buildingArea | number | 建筑面积（㎡） |
| buildingOvergroundArea | number | 地上建筑面积（㎡） |
| spaceAreaConditionUp | number | 地上空调房间面积（㎡） |
| buildingHeight | number | 建筑高度（米） |
| buildingHeightUp | number | 地上建筑高度（米） |
| shapeCoefficient | number | 建筑体形系数 |
| isGlassCurtainWall | boolean | 是否玻璃幕墙（四朝向平均窗墙比均≥0.4 视为玻璃幕墙） |
| mainFunctionRoomAreaScale | number | 主要功能房间面积占比（0~100，百分比） |
| eastWinWallScale | number | 东向窗墙比（0~1小数） |
| southWinWallScale | number | 南向窗墙比（0~1小数） |
| westWinWallScale | number | 西向窗墙比（0~1小数） |
| northWinWallScale | number | 北向窗墙比（0~1小数） |
| scaleKaiJianEast | number | 东向开间比（0~1小数） |
| scaleKaiJianSouth | number | 南向开间比（0~1小数） |
| scaleKaiJianWest | number | 西向开间比（0~1小数） |
| scaleKaiJianNorth | number | 北向开间比（0~1小数） |
| roofAvgK | number | 屋顶平均传热系数（W/m²K） |
| roofArea | number | 屋顶面积（㎡） |
| eastWallAvgK | number | 东向外墙平均传热系数 k |
| southWallAvgK | number | 南向外墙平均传热系数 k |
| westWallAvgK | number | 西向外墙平均传热系数 k |
| northWallAvgK | number | 北向外墙平均传热系数 k |
| eastWindowAvgK | number | 东向外窗平均传热系数 k |
| southWindowAvgK | number | 南向外窗平均传热系数 k |
| westWindowAvgK | number | 西向外窗平均传热系数 k |
| northWindowAvgK | number | 北向外窗平均传热系数 k |
| eastWindowAvgSW | number | 东向外窗平均遮阳系数（0~1小数） |
| southWindowAvgSW | number | 南向外窗平均遮阳系数（0~1小数） |
| westWindowAvgSW | number | 西向外窗平均遮阳系数（0~1小数） |
| northWindowAvgSW | number | 北向外窗平均遮阳系数（0~1小数） |
| mainStdFlrHouseTypeNum | int | 主要标准层户型数量（居建用） |
| mainStdFlrMainHouseTypeArea | number | 主要标准层主力户型面积（居建用，㎡） |
| systemTypeIDs | int | 系统类型ID |

若 `buildingFunction` 为公共建筑（办公/医院/学校等），`mainStdFlr*` 两个字段省略。
若某个字段用户未提供，不传入该字段，服务端会根据已有数据补齐。但是，调用时传入字段填得越多，预测越准。

## 统一入口函数：LoadForecast

为便于 agent 调用，将上述流程封装为统一入口 `LoadForecast`，步骤如下：

### 第 1 步：确定城市信息

接口支持直接传 `cityId` 或 `cityName`，**无需解析**：用户给哪个就传哪个，二选一、必传其一；若两者都给了，`cityId` 优先。

### 第 2 步：组装 Query 参数

必传/常用：
- `load_type`：负荷类型，1-热；2-冷；3-冷+热（默认 3）。
- `output_type`：输出精度，1-逐日（默认）；2-逐时。

可选温度阈值参数（**是 Query 参数，不是 Body 字段**；仅在用户给出了启动/制热等相关温度时传入，否则留空用默认值，见「Query 参数」表）：
- `min_temp_startup_condition`：启动空调的最低温度
- `min_temp_startup_heating`：室外侧名义制热工况
- `max_temp_startup_heating_residence`：户用建筑启动采暖最高温度
- `max_temp_startup_heating_industrial_commercial`：工商业建筑启动采暖最高温度

温度参数通过 `-p/--params` 传入，可多个用 `&` 拼接，如 `-p "min_temp_startup_condition=26&max_temp_startup_heating_residence=16"`。

### 第 3 步：组装 Body

使用用户明确给出的字段，构造 JSON 请求体（body 中只包含用户提供的字段，其余由服务端补齐）。将第 1 步确定的城市填入 `cityId` 或 `cityName` 字段。

### 第 4 步：发起 POST 请求

调用脚本 `references/load-forecast/scripts/load_forecast.py` 发起请求（token 认证与请求地址由脚本内部处理，无需传参）。脚本会在**运行目录**生成（文件名随 `-ot` 输出精度而定）：
- `load_forecast_result_daily.json` / `load_forecast_result_hourly.json`：服务完整返回（负荷数组 + 参数回显）；
- `load_forecast_daily.png` / `load_forecast_hourly.png`：冷/热负荷曲线图（仅冷/仅热时只画一条，需 matplotlib）。

终端打印：峰/谷/均值、月度汇总表与文件路径。

调用方式（`--body` 支持文件路径或 JSON 字符串，推荐直接传字符串，免去写文件步骤）：

```powershell
# 方式一：直接传 JSON 字符串（推荐）；参数再多也无需写文件，命令行长度足够容纳全部字段
python references/load-forecast/scripts/load_forecast.py --body "{\"buildingFunction\":\"办公\",\"cityId\":101,\"buildingArea\":4000}" -lt 3 -ot 1

# 方式二：先写入临时 JSON 文件再传文件路径（参数特别多或包含复杂字符串时可改用此方式）
python references/load-forecast/scripts/load_forecast.py --body <body.json> -lt 3 -ot 1
```

说明：`--body` 若是存在的文件路径则按文件读取，否则按 JSON 字符串解析（脚本内置判断）。即使把全部可选参数都传齐，body 也只有数千字符，远低于命令行长度上限，传入全部参数可让预测更准。

参数说明：
- `--body`：必填，body JSON 的文件路径或 JSON 字符串。
- `-lt`/`--load_type`：负荷类型，1-热；2-冷；3-冷+热（默认 3）。
- `-ot`/`--output_type`：输出精度，1-逐日（默认）；2-逐时。
- `-p`/`--params`：额外的 query 参数，如 `"min_temp_startup_heating=-12"`（可选）。

### 第 5 步：解析并转成中文结果

- 以终端打印的峰/谷/均值、月度汇总表为主要汇报内容，整理成中文给用户。
- 若需逐日/逐时明细，读取对应的 `load_forecast_result_daily.json` 或 `load_forecast_result_hourly.json`：`model_hot` / `model_cool` 是数组，每一项 `{ "date": "01-01" 或 "01-01 08:00", "value": 5.33 }`；`building_info` 为预测时实际使用的参数回显。
- `load_type=1` 时 `model_cool` 为 null；`load_type=2` 时 `model_hot` 为 null；`load_type=3` 时两者都有。
- 向用户汇报时**不要**直接展示原始请求参数、token 或错误码。

## 响应结构说明

| 字段 | 类型 | 说明 |
|------|------|------|
| model_hot | array | 典型气象年热负荷（逐日/逐时），元素为 `{date, value}` |
| model_cool | array | 典型气象年冷负荷（逐日/逐时），元素为 `{date, value}` |
| building_info | object | 预测时使用的参数回显（含 building_id 等） |

## 注意

脚本或服务端的报错需**转成中文**转述给用户，**不要**直接展示 token、请求地址、HTTP 状态码或原始异常信息。常见情况的提醒方式：
- **token 未配置或无效**（脚本提示找不到 token，或服务端返回 401/403）：提醒用户「负荷预测接口认证未通过，请在 `.env` 中配置正确的 `HVAC_FORECAST_TOKEN` 后重试」，不展示具体错误码。
- **网络不可达 / 接口超时**：提醒用户「负荷预测服务暂时无法访问，请稍后重试或检查网络」。
- **cityName 无效 / 城市不存在**（服务端返回城市相关错误）：提醒用户确认城市名称是否填写正确，或改用 `cityId` 传入。
- **其它非预期失败**：如实告知用户本次未能完成预测，提示可补充更多建筑参数后重试，避免盲目反复尝试。

调用接口时传入的信息越多，预测结果越准确。
