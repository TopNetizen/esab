---
name: model-tools
description: |
  用于处理建筑模型实体对象的基础操作，提供模型对象级别的创建、查询、修改、删除及属性管理能力。
  本技能不具备上下文语义解析能力。当用户使用「当前」「现在」「目前」「选中的」「打开的」等指代性描述时，应通过 context-tools 解析后再执行该技能。
  触发条件：
  1. 当用户需求涉及直接操作具体模型实体，且操作范围为单个或少量对象时触发此技能。
  2. 适用于对已有模型对象进行定位、查看、编辑、创建或删除等基础模型操作。
  禁止触发条件：
  1. 当用户需求涉及楼层（普通层）的删除、增加、调整顺序等楼层体系变更操作时，不使用本技能。此类需求应通过 advanced-tools 的楼层组装流程处理。
---

# BIM 模型类工具集（Skill）

## 1. 概述

本 Skill 封装 BIM 模型实体构件基础操作接口，覆盖构件创建、信息查询、属性编辑、实体删除等能力。

适用于目标明确、作用对象为单个或少量构件的精细化建模交互场景。所有操作均以实时最新模型数据为准定位目标实体，并严格遵循模型对象操作约束执行。

---

## 2. 工具列表

### 单体建筑

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreateBuilding` | 创建建筑 | `references/building.md` |
| `SetBuilding` | 修改建筑 | `references/building.md` |
| `GetBuildings` / `GetBuilding` | 查询（当前工程下所有建筑 / 单栋建筑）| `references/building.md` |

### 标准层

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreateStandardFloor` | 创建标准层 | `references/standard-floor.md` |
| `DeleteStandardFloor` | 删除标准层 | `references/standard-floor.md` |
| `SetStandardFloor` | 修改标准层 | `references/standard-floor.md` |
| `GetStandardFloors` / `GetStandardFloor` | 查询（指定建筑下所有标准层 / 单个标准层） | `references/standard-floor.md` |

### 普通层（楼层）

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `GetCommonFloors` / `GetCommonFloor` | 查询（指定建筑下所有普通层 / 单个普通层） | `references/common-floor.md` |

### 房间

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `SetRoom` | 修改房间 | `references/room.md` |
| `GetRooms` / `GetRoom` | 查询（指定建筑下所有房间 / 单个房间） | `references/room.md` |

### 普通墙

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreateWall` | 创建墙 | `references/wall.md` |
| `DeleteWall` | 删除墙 | `references/wall.md` |
| `SetWall` | 修改墙 | `references/wall.md` |
| `GetWalls` / `GetWall` | 查询（指定标准层下所有墙 / 单个墙） | `references/wall.md` |

### 幕墙

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreateCurtainWall` | 创建幕墙 | `references/curtain-wall.md` |
| `DeleteCurtainWall` | 删除幕墙 | `references/curtain-wall.md` |
| `SetCurtainWall` | 修改幕墙 | `references/curtain-wall.md` |
| `GetCurtainWalls` / `GetCurtainWall` | 查询（指定标准层下所有幕墙 / 单个幕墙） | `references/curtain-wall.md` |

### 门

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreateDoor` | 创建门 | `references/door.md` |
| `DeleteDoor` | 删除门 | `references/door.md` |
| `SetDoor` | 修改门 | `references/door.md` |
| `GetDoors` / `GetDoor` | 查询（指定标准层下所有门 / 单个门） | `references/door.md` |

### 窗

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreateWindow` | 创建窗 | `references/window.md` |
| `DeleteWindow` | 删除窗 | `references/window.md` |
| `SetWindow` | 修改窗 | `references/window.md` |
| `GetWindows` / `GetWindow` | 查询（指定标准层下所有窗 / 单个窗） | `references/window.md` |

### 结构柱

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreatePillar` | 创建柱 | `references/pillar.md` |
| `DeletePillar` | 删除柱 | `references/pillar.md` |
| `SetPillar` | 修改柱 | `references/pillar.md` |
| `GetPillars` / `GetPillar` | 查询（指定标准层下所有柱 / 单个柱） | `references/pillar.md` |

### 屋顶

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreateRoof` | 创建屋顶 | `references/roof.md` |
| `DeleteRoof` | 删除屋顶 | `references/roof.md` |
| `GetRoofs` / `GetRoof` | 查询（指定标准层下所有屋顶 ID / 单个屋顶） | `references/roof.md` |

### 遮阳

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `CreateShading` | 创建遮阳 | `references/shading.md` |
| `DeleteShading` | 删除遮阳 | `references/shading.md` |
| `GetShadings` / `GetShading` | 查询（某个实体中所有遮阳 / 单个遮阳） | `references/shading.md` |

### 体量建筑

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `SetBuildingMass` | 修改体量建筑 | `references/mass-building.md` |
| `GetBuildingMasses` | 查询当前工程中所有体量建筑 | `references/mass-building.md` |

### 道路

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `SetRoad` | 修改道路 | `references/road.md` |
| `GetRoads` | 查询所有道路 | `references/road.md` |

### 其它

| 工具名称 | 功能说明 | 详细文档 |
|----------|---------|---------|
| `GetComponentSeriesNames` | 查询指定构件类型的可用样式名称列表 | `references/helper.md` |

---

## 3. 典型工作流

### 标准建模流程

1. 创建建筑。
2. 创建标准层。
3. 编辑标准层，创建基础模型实体。
   基础实体应优先创建不依赖其他构件的对象，例如：
   - 普通墙
   - 幕墙
   - 柱
   - 楼板
   - 屋顶
4. 创建依附构件。
   对于依附宿主的构件（如门、窗及其他附属构件），必须满足：
   - 宿主构件已提前创建。
   - 创建时传入正确的宿主 ID。
   - 禁止创建不存在宿主的依附构件。
5. 完成标准层建模后，调用 `AssembleFloors` 将标准层组装为实际楼层。
6. 建模完成后进行模型验证，确认：
   - 楼层结构是否正确。
   - 标准层与楼层的关联关系是否正确。
   - 模型对象引用关系是否完整。

---

## 4. 必须遵循

1. 工具首次调用前必须阅读对应工具文档，并严格按照文档中的参数定义、格式要求填写 `parameters`。禁止臆测参数含义、遗漏必填参数或传入未定义字段。
2. 批量删除操作必须在用户二次确认后执行，不得因用户明确表达 “删除全部” 而跳过确认步骤，以避免误删风险。
3. 当执行某类构件的批量删除操作后，必须通过查询工具复核删除结果，确保相关构件已被完全清除。

---
