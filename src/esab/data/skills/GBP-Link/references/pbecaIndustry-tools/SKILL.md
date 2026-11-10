---
name: pbecaIndustry-tools
description: 工业节能设计及计算分析工具集。当用户请求智能设置材料、材料编辑设置材料、遮阳设置、规定性指标计算、权衡计算、生成报告书时触发此技能。
---

# 工业节能计算工具集 (PbecaIndustry Tools)

本SKILL提供建筑节能设计及计算的操作能力，包括智能设置材料、遮阳设置等功能。MCP 调用规范详见主技能 `SKILL.md`。

**工业节能计算的包含的功能包括：**
1. 建筑材料设置，包括：智能设置材料
2. 遮阳设置
3. 规定性指标计算
4. 权衡计算
5. 生成规定性指标报告书
6. 生成权衡计算报告书
7. 规定性指标计算结果获取
8. 权衡结果获取
9. 可选遮阳类型获取
10. 遮阳类型所需参数获取

### 特别说明
1. 设置材料如果获取到的建筑类型是2，即为既有公建也有居建，需要用户手动选择设置公建还是居建材料，并公建返回0，居建返回1。
2. 回复用户时，**不要**直接展示传给工具的参数和工具返回的错误代码，而要将其转换成中文进行回复。
3. 进行计算（批量计算除外）之前需要询问当前标准选择是否正确，若不正确询问是否需要更换标准（GetChoiceStandards）让用户选择新标准（SetStandard）。
4. 调用规定性指标计算后，获取规定性结果和强条结果，规定性达标无需权衡计算，强条不达标不可权衡计算。
---

## 指令映射表

`command` 参数允许的值及其对应的功能说明如下：


### 材料设置
| Command Value | 功能描述 |
| :--- | :--- |
| `AgentGetBuildPH` | 获取当前建筑类型 接口说明详见references/AgentGetBuildPH.md|
| `MatchMaterialSolution` | 获取好后根据当地材料进行设置，并满足限值要求  接口说明详见references/MatchMaterialSolution.md|

> 本组命令基于软件内置材料库进行智能匹配，无需外部数据。若用户已有节能报告书（.doc/.docx/.rtf），需从报告书中提取材料 JSON 再应用到模型，改走 `references/materialhandle-tools/SKILL.md` 的 `GetAndSetMaterial` 流程。

### 遮阳设置
| Command Value | 功能描述 |
| :--- | :--- |
| `GetChoiceShades` | 获取当前建筑可选遮阳类型 接口说明详见references/GetChoiceShades.md|
| `GetShadeDetailedInfo` | 获取设置所选遮阳类型需要的参数 接口说明详见references/GetShadeDetailedInfo.md|
| `ShadeDetailedSetting` | 进行遮阳设置，必须加载了bdls，且有单栋建筑。接口说明详见references/ShadeDetailedSetting.md|

### 规定性指标计算
| Command Value | 功能描述 |
| :--- | :--- |
| `CalcStaticFunIndustry` | 进行规定性指标计算，必须加载了bdls，且有单栋建筑，从“规定性指标计算结果获取”工具取结果以表格形式展示，不要打开结果分析和生成报告书。接口说明详见references/CalcStaticFunIndustry.md|

### 权衡计算
| Command Value | 功能描述 |
| :--- | :--- |
| `CalcEnergyFunIndustry` | 进行权衡计算，必须加载了bdls，且有单栋建筑，且强条达标，不要打开结果分析和生成报告书，从“权衡结果获取”工具取结果以表格形式展示。接口说明详见references/CalcEnergyFunIndustry.md|

### 规定性指标报告书生成
| Command Value | 功能描述 |
| :--- | :--- |
| `CreateReportStaticIndustry` | 进行规定性指标报告书生成，必须加载了bdls，且有单栋建筑。接口说明详见references/CreateReportStaticIndustry.md|

### 权衡报告书生成
| Command Value | 功能描述 |
| :--- | :--- |
| `CreateReportEnergyIndustry` | 进行权衡计算报告书生成，必须加载了bdls，且有单栋建筑。接口说明详见references/CreateReportEnergyIndustry.md|

### 规定性指标结果获取
| Command Value | 功能描述 |
| :--- | :--- |
| `GetStaticFunResultIndustry` | 获取规定性指标计算后的结果，必须加载了bdls，且有单栋建筑。接口说明详见references/GetStaticFunResultIndustry.md|

### 权衡结果获取
| Command Value | 功能描述 |
| :--- | :--- |
| `GetEnergyResultIndustry` | 获取权衡计算后的结果，必须加载了bdls，且有单栋建筑。接口说明详见references/GetEnergyResultIndustry.md|

### 获取当前所选标准
| Command Value | 功能描述 |
| :--- | :--- |
| `GetCurStandard` | 
获取当前所选标准，必须加载了bdls，且有单栋建筑。接口说明详见references/GetCurStandard.md|

### 获取当前可选标准
| Command Value | 功能描述 |
| :--- | :--- |
| `GetChoiceStandards` | 获取当前可选标准，必须加载了bdls，且有单栋建筑。接口说明详见references/GetChoiceStandards.md|

### 设置标准
| Command Value | 功能描述 |
| :--- | :--- |
| `SetStandard` | 
设置标准，必须加载了bdls，且有单栋建筑。接口说明详见references/SetStandard.md|

---
