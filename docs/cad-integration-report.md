# ESAB 0.4.0a1 本地 CAD 插件测试报告

> 记录 0.4.0a1 在 Windows 参照机上完成的 CAD 联调，以及全部 15 个连接入口的假连接审计。
> 脚本与原始记录随仓库发布，路径见下表。

| 报告内引用 | 仓库路径 |
|---|---|
| `adapter_audit.py` / `adapter_audit.json` | `tools/adapter_audit.py` / `tools/adapter_audit.json` |
| `false_positive_probe.py` | `tools/false_positive_probe.py` |
| `cad_bridge_test.py` / `com_layer_test.py` | `tools/cad_bridge_test.py` / `tools/com_layer_test.py` |
| 浩辰端到端脚本及其探测脚本 | `tools/gstarcad_e2e_test.py` / `tools/gstarcad_probe.py` / `tools/gstarcad_com_probe.py` |
| 实机截图 | `docs/images/gstarcad-e2e-result.png` |

测试时间：2026-11-10
测试对象：`esab` 0.4.0a1 源码树（解包副本，未改动开发者原有的工作目录）
测试机：Windows 本机，Python 3.13.16，PowerShell 7.6.4

## 1. 结论

**插件本体可用；本机没有 AutoCAD，改用浩辰CAD 2027 实机测试后，在打好“CAD 产品 ProgID 兼容”补丁的条件下全部通过（详见第 7、8 节）。**

- 插件安装、自测、MCP 服务、Python 持久执行、COM 调用链均验证通过（用 Excel 16.0 做了真实 COM 读写验证）。
- 本机 AutoCAD 2019 已被卸载或文件被删除，只剩注册表残留，`AutoCAD.Application` 无可执行程序可用。
- 发现插件三处缺陷（见第 4 节），`connect_cad()` 在没有 CAD 时**误报连接成功**属于必须先修的问题；pyautocad 硬编码 `AutoCAD.Application` 导致浩辰/中望不可用的问题已在第 7 节修复并实测。

## 2. 通过的测试项

| # | 测试项 | 方法 | 结果 |
|---|---|---|---|
| 1 | 安装 | `pip install -e ".[win32,test]"` | 通过，`esab 0.4.0a1`，comtypes / pywin32 / pyautocad 0.2.0 齐备 |
| 2 | 自带测试 | `python -m pytest tests -q` | 通过，23 项全绿 |
| 3 | MCP 启动 | `python -m esab agent --skills-root ...`（stdio） | 通过，`esab-runtime 0.4.0a1` 初始化成功 |
| 4 | 工具注册 | `list_tools` | 通过，`python_executor / use_skill / cancel_execution / list_software_adapters` |
| 5 | 软件清单 | `list_software_adapters` | 通过，CAD 条目 kind=com，入口 `adapters.hosts.connect_cad` |
| 6 | 技能读取 | `use_skill("AutoCAD-Link")` | 通过，返回 SKILL.md 全文 6224 字符，is_error=False |
| 7 | COM 执行链 | `python_executor` 内 `DispatchEx("Excel.Application")` | 通过，Excel 16.0，A1 写入并读回一致，`=2*3+4` 计算得 10.0，关闭不留存盘 |
| 8 | 会话持久化 | 第二次 `python_executor` 读取上一次的变量 | 通过，变量 `_SAB_PERSIST` 跨调用有效（同一 Python 进程） |

## 3. 未通过的测试项：CAD 连接

`python_executor` 中执行 CAD 绘图脚本，第 1 步失败：

```
STEP1 connected
GetActiveObject('AutoCAD.Application') -> OSError: [WinError -2147221021] 操作无法使用
CreateObject('AutoCAD.Application')    -> OSError: [WinError -2147221164] 没有注册类
```

错误码含义：`0x800401E3 MK_E_UNAVAILABLE`（无运行实例）、`0x80040154 REGDB_E_CLASSNOTREG`（类未注册）。

根因证据：

| 检查项 | 结果 |
|---|---|
| 卸载项 `AutoCAD 2019` 23.0.46.0 | 仍存在，InstallLocation = `D:\新建文件夹\CAD2019\cad\AutoCAD 2019\` |
| 该目录 / `acad.exe` | **不存在**（`Test-Path` = False；全盘 D: 递归 4 层、C:\Program Files 均无 `acad.exe`） |
| `HKLM\SOFTWARE\Classes\AutoCAD.Application` | **未注册**（只有 HKCU 下一个无 CLSID 的空壳） |
| `AutoCAD.Application.23` | 已注册，CLSID `{4AC6DFE1-607B-45B2-B289-D7FBCD44169C}` |
| 该 CLSID 的 LocalServer32 | `D:\新建文件夹\CAD2019\cad\AutoCAD 2019\acad.exe /Automation` → 目标文件不存在 |
| 其他 CAD（浩辰 / 中望） | `GstarCAD.Application`、`ZWCAD.Application` 均未注册 |

即：注册表里留着一套指向已消失文件的 CAD 自动化注册，ProgID `AutoCAD.Application`（pyautocad 用的就是它）也没有 CurVer 链，因此直接报“类未注册”。

## 4. 测试中发现的插件缺陷

### 4.1 `connect_cad()` 假成功（建议优先修）

`adapters/hosts.py::connect_cad` 只要 `Autocad(...)` 构造不抛异常就返回 `ok=True / live_verified=True`，而 pyautocad 0.2.0 的构造是**惰性**的：`Acad` 对象创建后内部 `_app` 仍为 `None`，真正连 COM 发生在首次访问 `acad.app` 时。实测：

```
python -c "from pyautocad import Autocad; a=Autocad(create_if_not_exists=False, visible=True); print(a._app)"
-> None
connect_cad() -> ok=True, message='已连接正在运行的 CAD。', live_verified=True   # 此时本机根本没有 CAD
```

后果：任何按 `connect_cad()` 结果判断“已连上 CAD”的上层逻辑都会误判，后续绘图代码才在 `acad.app` 处崩掉，错误位置与真实原因错位。

建议：返回值前强制探活一次，例如

```python
try:
    acad = Autocad(create_if_not_exists=False, visible=True)
    version = acad.app.Version        # 真正触发 COM 连接
except Exception as exc:
    return ConnectResult(ok=False, ...)
```

### 4.2 技能文档与随包 pyautocad 实际接口不一致

`data/skills/AutoCAD-Link/SKILL.md` 要求按下列写法连接和取常量：

```python
acad.connection.selected_by / .display_name / .progid / .was_created
acad.constants.acAllViewports
CadSelectionRequiredError / CadApplicationBusyError / ...
```

实测随包依赖 `pyautocad 0.2.0` 的 `Autocad` 只有：
`app, doc, model, ActiveDocument, Application, iter_objects, iter_objects_fast, iter_layouts, get_selection, find_one, prompt, aDouble, aInt, aShort, best_interface`
——没有 `connection`、没有 `constants`、没有任何自定义异常。
`import pyautocad` 里也没有这些异常类。

后果：agent 照 SKILL.md 写的连接代码第一步就 AttributeError，技能文档描述的是一套增强版 pyautocad，而包声明的依赖只是 PyPI 原版 0.2.0。

### 4.3 `WORKSPACE_DIR` 未注入

`runtime/builtins.py::install` 只注入 `connect_to_server / disconnect_server / is_server_connected / function_search / use_skill / connect_to_plants / STATE`，没有 `WORKSPACE_DIR`；但 `data/skills/STAADPro-Link/SKILL.md` 明确写着“python_executor 已注入 `WORKSPACE_DIR`”。实测在 `python_executor` 里引用它直接 `NameError: name 'WORKSPACE_DIR' is not defined`。

## 5. 复现与下一步

已留下的可重跑脚本（均在 `tools/` 下）：

- `tools/cad_bridge_test.py`：以 MCP 客户端身份拉起插件 → `list_software_adapters` → `use_skill` → `python_executor` 连 CAD 并绘制直线/圆/闭合多段线/文字/对齐标注 → 第二次调用读回图元校验。脚本内含保护逻辑：若当前图纸不是空白 `Drawing1`，会新建空白图纸再画，且不保存，不动用户既有图纸。
- `tools/com_layer_test.py`：COM 层与会话持久化验证。

CAD 恢复可用后的执行方式（任选其一）：

1. 重装 AutoCAD（或浩辰/中望），启动后再跑 `python tools/cad_bridge_test.py`；
2. 若改用浩辰/中望，需要同时让 ProgID 可解析（pyautocad 固定用 `AutoCAD.Application`），否则同样报类未注册；
3. 先修 4.1 的假成功问题再测，否则 CAD 未启动时也会“显示连接成功”。

## 6. CAD 连接须同时成立的 6 个前置条件

| # | 条件 | 不满足时的表现 | 本机现状 / 验证命令 |
|---|---|---|---|
| 1 | CAD 主体真实存在 | `Test-Path` 为假，或加载即退出 | 已证伪：acad.exe 不存在 |
| 2 | 通用 ProgID `AutoCAD.Application` 可解析（CurVer → 版本号） | `0x80040154 REGDB_E_CLASSNOTREG` | 本机只剩 `AutoCAD.Application.23`，无通用 ProgID——说明此前这套 2019 副本本身就没注册通用 ProgID（绿色/便携版常见）。命令：`reg query "HKLM\SOFTWARE\Classes\AutoCAD.Application" /v CurVer` |
| 3 | CAD 与 Python 同 UAC 权限级 | `0x80070005 E_ACCESSDENIED` / `CO_E_SERVER_EXEC_FAILURE` | 待装软件后验证：CAD 以管理员启动、脚本普通权限即失败 |
| 4 | CAD 空闲，无模态对话框或未完成命令 | `0x8001010A RPC_E_SERVERCALL_RETRYLATER`（服务忙） | 待验证：CAD 停在“输入文件名”“许可提示”时 COM 全部阻塞 |
| 5 | 首次 COM 启动能吃下 `/Automation`（许可服务在位） | `CoCreateInstance` 失败或长时间超时 | 本机 Autodesk License Service 7.1.4 仍在，但 CAD 主体缺失，未验证 |
| 6 | 代码写法与随包 pyautocad 0.2.0 匹配 | 第一步就 `AttributeError` | **已证伪（与是否有 CAD 无关）**：`acad.connection`、`acad.constants`、`CadSelectionRequiredError` 在 0.2.0 上都不存在，且 `Autocad` 没有 `__getattr__`，访问即抛错 |

结论：**第 1～4 条满足时，绘图与读回这一段基本必通**（`AddLine / AddCircle / AddPolyline / AddText / AddDimAligned / ZoomExtents` 都是 AutoCAD 跨版本稳定的 ActiveX 接口；本机 Excel 16.0 的 COM 实测也证明执行链和会话持久化本身没问题）。但“装了软件”只覆盖第 1 条，第 2 条在本机历史上就是不成立的，第 6 条与软件无关且当前必然失败。所以不能得出“必定通”。

第 6 条的可执行验证（无需 CAD，已跑过）：

```python
from pyautocad import Autocad
a = Autocad(create_if_not_exists=False, visible=True)
a.connection   # AttributeError: 'Autocad' object has no attribute 'connection'
a.constants    # AttributeError: 'Autocad' object has no attribute 'constants'
```

修法二选一：把 `AutoCAD-Link/SKILL.md` 改成 0.2.0 的原生写法（`acad.app.Version`、`acad.model`、`ActiveDocument.Regen` 等），或把随包依赖换成真正提供 `connection` / `constants` / 自定义异常的增强版 pyautocad。

## 7. 追加实测：浩辰CAD 2027（通过）

环境：浩辰CAD 2027 教育版，`app.Version = 27.00`，进程 `gcad.exe`（PID 17592，Drawing1.dwg）。

COM 注册现状（关键）：

| ProgID | 状态 | LocalServer32 |
|---|---|---|
| `AutoCAD.Application` | **未注册** | — |
| `GstarCAD.Application` | 已注册，CLSID `{5F40514B-B8A9-45A8-9DD6-485C47F21500}` | `D:\浩辰cad\浩辰CAD 2027\gcad.exe /Automation` |
| `GCAD.Application` | 已注册，同一个 CLSID | 同上 |
| `ZWCAD.Application` | 未注册 | — |

打补丁前的表现：

- 直连 `GstarCAD.Application`：完全正常（`Version 27.00`、`Name GstarCAD`、`ZoomExtents` 可调用）。
- 插件 `connect_cad()`：仍返回 `ok=True`（惰性假成功，见 4.1）。
- 插件技能写法 `pyautocad.Autocad().app`：`OSError [WinError -2147221021]` —— pyautocad 0.2.0 写死 `AutoCAD.Application`，在浩辰上必然连不上。

补丁内容（4 个文件，已合入源码）：

| 文件 | 改动 |
|---|---|
| `src/esab_shim/cad.py` | 新增。候选 ProgID 解析（AutoCAD → GstarCAD/GCAD → ZWCAD → BricsCAD），把 `comtypes.client.GetActiveObject/CreateObject` 对 `AutoCAD.Application` 的请求重定向到实际产品；返回前用 `app.Version` 做真实 COM 往返 |
| `src/esab/adapters/hosts.py` | `connect_cad()` 改调兼容层，返回产品名/版本/当前图纸，`ok=True` 即代表真连上 |
| `src/esab/runtime/builtins.py` | 向 `python_executor` 注入 `connect_cad()`，技能可直接调用 |
| `data/skills/AutoCAD-Link/SKILL.md` | 连接章节改为 0.2.0 真实可用的写法；删掉不存在的 `acad.connection`、`acad.constants`、自定义异常；补上四类真实错误的判断口径 |

补丁后实测结果（走完整 MCP stdio 通道：`use_skill` → `python_executor` → CAD）：

```
已连接 浩辰 CAD 27.00：Drawing1.dwg（GstarCAD.Application）
OPEN_DOCS: [(0, 'Drawing1.dwg'), (1, 'Drawing2.dwg')]
TEST_DOC: Drawing3.dwg | 新建后 ActiveDocument: Drawing3.dwg
ENTITY_DELTA: 0 -> 5 | 新增 5
图层 SAB-TEST 统计: {'AcDbLine': 1, 'AcDbCircle': 1, 'AcDb2dPolyline': 1, 'AcDbText': 1, 'AcDbAlignedDimension': 1}
  圆 圆心=(3000.0, 1500.0, 0.0) 半径=800.0
  文字='浩辰CAD 插件测试 SAB 0.4.0a1' 高=420.0
  对齐标注 文字覆盖=''
EXTMIN: (0.0, -901.25, 0.0) | EXTMAX: (8422.22, 8081.31, 0.0)
```

会话复用：第二次 `python_executor` 中 `SAB_ACAD` / `SAB_DOC` 对象仍有效，未重复连接。补丁后 `pytest tests -q` 仍 23 项全绿。实机截图：[`docs/images/gstarcad-e2e-result.png`](images/gstarcad-e2e-result.png)。

浩辰特有的两个行为（已写进技能注意事项）：

1. `Documents.Add()` 新建图纸后 **`ActiveDocument` 不会自动切到新图**，必须显式 `doc.Activate()`；否则后续读回会落到旧图（第一轮验证就踩到这个，查到空图）。
2. `AddPolyline` 在浩辰生成的是 **`AcDb2dPolyline`（重多段线）**，不是 `AcDbLightweightPolyline`；通过动态 COM 用 `getattr(obj, "Closed")` 读取会抛 `NameError: Name Closed not found`，读闭合状态要用 `try/except` 包住或改读坐标。

## 8. 结论修正：装软件 + 补丁后才通

| 前置条件 | AutoCAD 2019 时期 | 浩辰CAD 2027 + 补丁 |
|---|---|---|
| 1 软件主体存在 | ✗ | ✓ gcad.exe 在位 |
| 2 通用 ProgID 可解析 | ✗ 只有 `.23` | ✓ 由兼容层重定向到 `GstarCAD.Application` |
| 3 同 UAC 权限级 | 未测 | ✓ 同权限，`GetActiveObject` 成功 |
| 4 CAD 空闲 | 未测 | ✓ Drawing1 空闲，无模态框 |
| 5 `/Automation` 许可正常 | 未测 | ✓ 教育版 30 天试用期内，COM 启动正常 |
| 6 代码与依赖接口匹配 | ✗ | ✓ SKILL.md 已对齐 0.2.0 |

“有软件”本身不等于必定通：浩辰的通用 ProgID 同样不存在，第 6 条也与软件无关。补上产品解析层与文档修正后，本机跑通了从 MCP 工具调用到实际绘图的完整链路。

## 9. 其余 14 个软件接口的假连接审计

CAD 被证实存在假成功缺陷后，又检查了其余 14 个连接入口是否会在软件未运行或未安装时误报 `ok=True / live_verified=True`。审计分三步：运行时逐条真机调用 → 判据强度分级 → 对可疑判据做可控证伪实验。

### 9.1 运行时逐条实测（本机这 14 款软件均未安装或未运行）

| 接口 | 入口函数 | 结果 | 实际诊断 |
|---|---|---|---|
| PKPM | `connect_structural_pm` | ok=False | 没有找到运行中的 pkpmmcp 进程（PKPMMain.exe / PKPM.exe） |
| PKPM-CAE | `connect_structural_cae` | ok=False | 没有找到运行中的 cae-mcp 进程 |
| SAUSG | `connect_sausg` | ok=False | 没有找到运行中的 ssgmcp 进程 |
| GBP | `connect_gbp` | ok=False | 连接 `127.0.0.1:3333/GBPBECA3/galpserver/mcp` 失败（ExceptionGroup） |
| PlantS | `connect_plants` | ok=False | 没有找到运行中的 plantsmcp 进程 |
| BIMBase | `connect_bimbase` | ok=False | 没有找到运行中的 BIMBaseAI2PY_MCPServer 进程 |
| SAP2000 | `connect_sap2000` | ok=False | `OSError: [WinError -2147221005] 无效的类字符串`（CSI helper 未注册） |
| ETABS | `connect_etabs` | ok=False | 同上 |
| STAAD | `connect_staad` | ok=False | 未找到 openstaadpy，未找到任何 STAAD.Pro 安装 |
| MIDAS | `connect_midas` | ok=False | 缺少 `MIDAS_BASE_URL` / `MIDAS_MAPI_KEY` |
| Abaqus | `connect_abaqus` | ok=False | `127.0.0.1:48152` 拒绝连接（10061） |
| Tekla | `connect_tekla` | ok=False | DetectionError：未找到 Tekla |
| Rhino | `connect_rhino` | ok=False | 没有运行中的 Rhino，且注册表未找到已安装的 Rhino |
| CAD | `connect_cad` | **ok=True** | 已连接浩辰 CAD 27.00：Drawing3.dwg（上一轮补丁后的真实连接） |
| SketchUp | `connect_sketchup` | ok=False | `127.0.0.1:49999` 拒绝连接（10061） |

结论：**运行时层面除 CAD 外没有假成功**，14 个接口在软件缺失时全部给出针对性诊断，没有一个是“看起来成功”。完整原始记录见 `tools/adapter_audit.json`，可复跑脚本 `tools/adapter_audit.py`（每个入口独立子进程、45s 超时）。

“软件缺失时不误报”只是必要条件；软件装了但没开的情况更容易误判，因此又做了静态分级。

### 9.2 判据强度分级

**A 类：真实判据，有目标软件的实际回应**（与 CAD 修复后同级）

| 接口 | 判据 |
|---|---|
| PKPM / CAE / SAUSG / PlantS / BIMBase / GBP | 进程存在 → 枚举该 PID 的监听端口 → MCP `initialize` + `list_tools` 双程握手 |
| Abaqus | TCP 连通 + health 请求往返 + 响应 id 校验 |
| Tekla | `GetConnectionStatus()` + 程序版本 + 文档库年份一致性校验 |
| SketchUp | 桥接插件 status 往返 |
| CAD | 补丁后强制读 `app.Version` |

MCP 这一路还需排除“端口探测本身被骗”的可能：`port_discovery._probe_mcp` 只凭 HTTP 200/406/401/403 就认定该端口是 MCP，是个弱启发式。实测见 9.3-A：它确实被骗了，但 `connect_streamable` 仍报失败，因为最外层判据是真实握手，弱启发式只影响先试哪个端口。

**B 类：判据依赖软件自身语义，本机未安装、无法证伪**（详见 9.4）

`connect_sap2000` / `connect_etabs`、`connect_staad`、`connect_midas`。

**C 类：确认缺陷，已修**（详见 9.3 与 9.5）

`hosts.connect_official`、`software_link_kit/plants.py`、`software_link_kit/pkpm_calc.py`、`rhino_host.connect_rhino`。

### 9.3 可控证伪实验（脚本 `tools/false_positive_probe.py`）

| # | 实验设计 | 修复前 | 修复后 |
|---|---|---|---|
| A | 起一个假 HTTP 服务，对 `POST /mcp` 回 200 + 假 JSON-RPC | `_probe_mcp` 判定 True（被骗），`connect_streamable` ok=False | 不变，最终判据仍是真实握手 |
| B | 调 `connect_official`，传入一个返回字符串的函数（模拟“官方包装返回错误字符串”） | **ok=True, live_verified=True**，message“官方连接函数已返回” | ok=False，message“官方连接函数返回字符串（失败信号）” |
| C | 伪造 PlantS 进程存在（无任何实例、无 MCP 服务） | **返回 `{'connected': True}`** | 走真实 MCP 握手，抛 RuntimeError“没有找到运行中的 plantsmcp 进程” |
| D | PKPM 连接成功后取 `details["value"]` | 静默返回 `None`（details 里只有 url/pages/namespace） | 取不到就抛错并打印 `details` 现有键 |

三点补充：

1. **C 不是死代码**。`data/skills/PlantS-Link/SKILL.md` 第 28、39 行和 `scripts/IndustryCorridor.py` 第 21 行都直接 `from esab_shim.software_link_kit.plants import connect_to_plants`，而且该技能明确“禁止把 `connect_to_server('plantsmcp')` 当作首选入口”。也就是说 agent 最可能走的就是这条只看进程名的路径：PlantS 进程在、MCP 没起来时它会先报连接成功，等到调用注入工具才失败，错误位置与真实原因完全错位。
2. **B 是遗留函数**。`connect_official` 当前在 `CONNECTORS` 里没有调用方，属潜伏缺陷；只要以后有适配器复用它，就会重现最初 Rhino“未安装却 live_verified=true”那类误报。
3. **D 是第三种形态的假成功**：连接确实成功，但拿不到可调用对象，返回 `None` 而不报错。

### 9.4 三处必须在真机复核的判据

| 接口 | 疑点 | 复核方法 |
|---|---|---|
| SAP2000 / ETABS | `CreateObject("SAP2000v1.Helper"/"ETABSv1.Helper")` 只需 helper DLL 注册即成功（装了就有，与软件是否运行无关）；随后 `GetObject(...)` 若在未运行时**自动拉起实例**，则 ok=True 而 message 仍写“已附着正在运行的”，语义不准 | 装好、不打开软件，调 `connect_sap2000`，同时看 tasklist 是否新出现 sap2000.exe |
| STAAD | `os_analytical.connect()` 未见读模型/工程校验，不抛异常即成功 | STAAD 已运行但未打开模型时，看是否仍报 ok=True |
| MIDAS | `MidasClient.request` 遇 200 空 body 直接返回 `{}`，`/config/ver` 返回空也算连上 | 用返回空 body 的桩服务验证 |

另外发现一处文档/实现不匹配（与连接无关但会直接 ImportError）：`PKPM-Link/SKILL.md` 第 212 行 `from esab_shim.software_link_kit.pkpm_calc import RunPKPMAnalyse`，而 `pkpm_calc.py` 里并无 `RunPKPMAnalyse`，只有 `connect_pkpm_calc`。

### 9.5 本轮补丁（在 CAD 补丁基础上新增 4 文件改动）

| 文件 | 改动 |
|---|---|
| `src/esab/adapters/hosts.py` | `connect_official()`：官方函数返回字符串一律判失败，不再当成功 |
| `src/esab_shim/software_link_kit/plants.py` | 删除“只看进程名”的实现，改走运行时同款 MCP 发现 + 握手；失败抛 RuntimeError |
| `src/esab_shim/software_link_kit/pkpm_calc.py` | 取不到可调用对象时抛错并列出 `details` 键，不再静默 `None` |
| `src/esab/adapters/rhino_host.py` | 连接顺序改为 `GetActiveObject`（附着）优先，`EnsureDispatch/Dispatch`（会新建进程）退居其后；message 区分“已附着”与“已新建” |

补丁后 `pytest tests -q` 仍 23 项全绿；9.1 的全量审计复跑结果不变（14 个失败 + CAD 成功）。

### 9.6 结论

1. “有软件就必定通”不成立，CAD 已用浩辰证过一次；反过来，“没假报”也不等于“真连上”。
2. 15 个入口中，运行时层面只有 CAD 报成功且属真实连接，其余 14 个在软件缺失时判据正确。
3. 静态层面存在 **3 处确定的假成功逻辑**（`connect_official` 字符串当成功、PlantS 包装层只看进程名、pkpm_calc 静默 None），本轮已修；另有 **3 处判据需真机复核**（CSI 两个、STAAD、MIDAS 空响应），本机因软件未安装无法证伪，已在 9.4 给出可执行的复核步骤。
4. 判据强度上，Abaqus / Tekla / SketchUp / MCP 系 / 补丁后的 CAD 属同一档；最薄弱的是“只判进程或只判不抛异常”的路径。

