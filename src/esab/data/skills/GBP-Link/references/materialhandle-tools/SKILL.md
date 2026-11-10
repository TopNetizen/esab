---
name: becs-material-json
description: 生成 PKPM 材料 JSON（围护结构构造 / 外窗 / 门）。根据报告书类型自动选择解析器：RTF 文件或内容为 PKPM 的报告书用 MaterialRecognitionPBECA.py 解析；内容为 BECS/斯维尔/天正 的报告书用 MaterialRecognitionBEC.py 解析；统一入口 MaterialRecognitionDispatcher.py 自动识别路由，也可 --force 强制指定。当用户提到生成材料json、材料识别、材料提取、BECS报告书解析、斯维尔报告解析、天正报告解析、PKPM报告书解析、围护结构材料数据等需求时使用。
---

# 材料 JSON 生成（自动识别报告类型并路由）

解析建筑节能设计报告书（.doc / .docx / .rtf）→ 生成 PKPM 材料 JSON（struct 构造 / windows 外窗 / doors 门）。

## 报告类型识别与路由规则（硬性规则）

| 输入报告书 | 解析器 | 说明 |
|-----------|--------|------|
| 文件为 .rtf | `MaterialRecognitionPBECA.py` | 任何 .rtf 一律走 PKPM 解析（先转 .docx 再纯 Python 读取，见「性能与加速」） |
| 内容含 PKPM 特征（PKPM / PBECA / 规定性指标计算报告书 / 公共建筑节能计算分析报告书 等） | `MaterialRecognitionPBECA.py` | .doc / .docx 嗅探正文内容 |
| 内容含 BECS/斯维尔 特征（BECS / TH-BECS / 斯维尔 / Swell / 建筑节能设计报告书 等） | `MaterialRecognitionBEC.py` | 输入为 .doc/.rtf 时先经 Word 转 .docx（带缓存）再解析 |
| 内容含天正特征（天正 / 公共建筑节能计算报告书 / 围护结构基本组成 / T-Ec / TArch） | `MaterialRecognitionBEC.py` | 复用 BECS 解析核心（gen_mat2.py 已兼容天正模板），识别原因标注「（天正）」 |
| 无法识别 | `MaterialRecognitionBEC.py` | 默认按 BECS 解析（纯 Python 无 Word 依赖），打印告警 |

内容识别顺序：先匹配 PKPM 特征，再匹配 BECS/斯维尔，再匹配天正特征， 特征。可跳过识别强制指定：`--force-pbeca` / `--force-bec`。

## 输入参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| report | 是 | - | 报告书路径（.doc / .docx / .rtf） |
| --out | 否 | 报告书同目录 `<报告书主名>_材料.json` | 输出材料 JSON 路径 |
| --work-dir | 否 | 本技能 `references` 目录 | BECS 工作目录（存放 `gen_mat2.py` / `docx_parse.py`） |
| --force-pbeca | 否 | - | 强制使用 MaterialRecognitionPBECA |
| --force-bec | 否 | - | 强制使用 MaterialRecognitionBEC |
| --no-galp | 否 | 开启 | **[Galp 输出]** 关闭同步；默认生成成功后把材料 JSON 复制到 `%LOCALAPPDATA%\Galp\MaterialHandle.json` |
| --no-docx-cache | 否 | 开启缓存 | **[加速]** 关闭 `.doc/.rtf → .docx` 转换缓存；默认按 `(路径, mtime, size)` 缓存到 `%LOCALAPPDATA%\Galp\docx_cache`，命中时**完全不启动 Word** |
| --batch | 否 | - | **[2026-09-20]** 批量模式：`report` 传目录时遍历其中全部报告书，输出到 `<目录>\_test_out\<主名>_材料.json`，已存在产物自动跳过，批量模式固定不写 Galp |
| --force | 否 | - | **[2026-09-20]** 批量模式下重新生成已存在产物 |

用户提供自己的 work_dir（含 `gen_mat2.py` / `docx_parse.py`）时优先使用用户的目录；否则用本技能内置的 `references`。

## 执行步骤

1. 确定参数：`report`（必填）、`--out`（缺省用报告书同目录 `<主名>_材料.json`）、`--work-dir`（缺省用本技能 `references`）。
2. 运行统一调度脚本（PowerShell，路径含空格用双引号）：

   ```powershell
   python "<skill>/scripts/MaterialRecognitionDispatcher.py" "<报告书路径>" [--out "<输出json>"] [--work-dir "<目录>"] [--force-pbeca|--force-bec]
   ```

   等价函数式入口（import 后调用）：
   ```python
   import sys; sys.path.insert(0, r"<skill>/references/materialhandle-tools/scripts")
   from MaterialRecognitionDispatcher import dispatch
   dispatch(report=r"<报告书路径>", out_txt_path=r"<输出json>", work_dir=r"<目录>", force=None)
   # galp=True（默认）时自动同步到 %LOCALAPPDATA%\Galp\MaterialHandle.json；传 galp=False 关闭
   ```
3. 调度脚本自动完成：类型识别（rtf / 内容嗅探）→ 选择解析器 → 生成材料 JSON：
   - **PKPM 路径**（`MaterialRecognitionPBECA.py`）：`.docx` 直接纯 Python 解析；`.doc/.rtf` 先经**一次** Word 会话完成「类型嗅探 + 转 .docx（带缓存）」，再纯 Python 解析材料依据表 / 围护构造热工表 / 门窗 → 输出标准 JSON（无注释）；覆盖输出前先时间戳备份旧文件。纯 Python 后端异常时自动回退 Word COM 直读原始文件。
   - **BECS 路径**（`MaterialRecognitionBEC.py`）：`precheck`（缺 docx / gen_mat2.py / docx_parse.py 时抛错）→ `patch_gen_mat_script`（注入 CATE_RENAME 映射生成 gen_mat3.py，重复运行幂等；写盘前自动清除目标文件只读属性）→ `backup_old_output`（时间戳备份，绝不覆盖历史基线）→ `run_gen_mat3`（解析 docx）→ `diff_and_report`（差异行、全部 cateName、构造 K/RT/D 报表；读取输出时编码自适应 UTF-8→GBK）。
4. **[Galp 输出]（默认开启）**：生成成功后，调度脚本自动把主产物 JSON 复制到当前用户 `%LOCALAPPDATA%\Galp\MaterialHandle.json`（目录不存在会自动创建，拷贝过去的文件固定重命名为 `MaterialHandle.json`）；加 `--no-galp` 可关闭。复制失败只告警，不影响主产物交付。
5. 向用户汇报识别结果（报告类型与原因）、产物路径与统计（材料数 / 构造数 / 外窗数 / 门数），并告知 Galp 同步结果，交付输出 JSON。
6.输出JSON后调用GALP功能获取和设置材料‘GetAndSetMaterial’功能进行应用。

## 产物

| 文件 | 位置 |
|------|------|
| 材料 JSON（主产物） | `--out` 指定路径（缺省 `<报告书主名>_材料.json`）；BECS 路径会同时复制一份到 `work_dir/` |
| **[Galp 输出]（默认开启）** | `%LOCALAPPDATA%\Galp\MaterialHandle.json`（主产物的副本，固定文件名，目录不存在自动创建） |
| 原文件备份 | BECS 路径：`<work_dir>/<主名>_材料_原类别_<时间戳>.json`；PKPM 路径：`<输出同目录>/<主名>_材料_原_<时间戳>.json` |
| 派生脚本 | BECS 路径：`<work_dir>/gen_mat3.py` |
| **[加速] .docx 转换缓存** | `%LOCALAPPDATA%\Galp\docx_cache\<key>_<主名>.docx` 及同名 `.json`（缓存的嗅探结论）；`key = sha1(绝对路径\|mtime\|size)[:16]`，源文件一改键就变，不会读到脏缓存。可直接删除整个目录清理 |

## Galp 输出（MaterialHandle.json）说明

> **[Galp 输出] 能力（2026-09-15 新增）**：为了让 PKPM 软件侧能固定读取到最新材料数据，调度脚本在生成成功后会额外做一次"同步到 Galp"：
>
> - **目标路径**：`%LOCALAPPDATA%\Galp\MaterialHandle.json`（`LOCALAPPDATA` 缺失时回退 `~\AppData\Local`，即 `C:\Users\<当前用户>\AppData\Local\Galp\MaterialHandle.json`）
> - **行为**：目录不存在则自动创建；将本次生成的材料 JSON **复制**过去并固定重命名为 `MaterialHandle.json`（主产物原路径保留不动）
> - **关闭方式**：命令行 `--no-galp`；函数入口 `dispatch(..., galp=False)`
> - **失败处理**：同步失败只打印 `[Galp]` 告警，不影响主产物生成与交付
> - **实现位置**：`scripts/MaterialRecognitionDispatcher.py` 中标注 `[Galp 输出]` 的代码段

## BECS 路径报告兼容性（BECS / 斯维尔）

解析核心（`references/gen_mat2.py`）对两类报告书均做了兼容：

| 差异点 | BECS（旧） | 斯维尔 Swell（新支持） |
|--------|-----------|------------------------|
| 构造表表头 | `材料名称` | `材料名称（由上到下）/（由外到内）`，厚度列 `厚度δ` |
| 构造表汇总行 | `各层之和` | `各层之和∑`；另有 `考虑热桥后K= 2.08 + 249.51/1832.76 = 2.21` 公式行（自动跳过） |
| K 公式表面热阻 | `K=1/(0.15+∑R)`（冬季，RE=0.04/RI=0.11） | `K=1/(0.16+∑R)`（夏季，RE=0.05/RI=0.11），从公式总阻值自动推导 |
| 外窗表遮阳列 | `自遮阳系数` → SHGC = SC×0.87 | `太阳得热系数`（直接给 SHGC）→ SC = SHGC/0.87 |
| 外窗命名 | `玻璃+气体-窗框[Kf=…,框面积…%]` | `12A钢铝单框双玻窗（平均）` 无分隔命名，自动解析 12A→12mm 空气层、双玻→2 层玻璃、钢铝→窗框材料 |
| 材料表单位行 | - | `W/(m.K)` 等单位行与空行自动跳过 |
| 简要说明定位 | - | 文档目录(TOC)中也有「围护结构作法简要说明…体形系数」，自动取**最后一次出现**（正文节），避免误匹配目录 |

## BECS 路径报告兼容性（天正 T-Ec）

解析核心（`references/gen_mat2.py`）已支持天正《公共建筑节能计算报告书》（.doc/.docx，如"围护结构基本组成"以「第N层：材料， 厚度 Xmm」段落描述、构造层表随附）：

| 差异点 | BECS/斯维尔 | 天正 T-Ec（新支持） |
|--------|------------|---------------------|
| 构造表表头 | `材料名称` / `材料名称（由上到下）` | `各层材料名称`（识别放宽为含「材料名称」且含「厚度」列） |
| 材料表 | 有「工程材料表」（导热系数/蓄热系数等） | **无独立材料表**，材料参数直接取构造表数值（不再报错） |
| 构造表汇总行 | `各层之和∑` | `合    计` |
| 表面热阻 | `K=1/(0.15+∑R)` / `K=1/(0.16+∑R)` 单行公式 | 两行式：`屋面主体部位传热阻 \| R0=Ri+∑R+Re = 0.11` + `屋面主体部位传热系数 \| K = 1/R0 =0.15`（第二列），按 R[ie] 判内外 |
| 外窗表 | `序号 \| 构造名称 \| …自遮阳系数/太阳得热系数…` | `类别 \| 类型 \| 传热系数 \| 遮阳系数 \| 可见光透射比`（遮阳系数=SC→SHGC=SC×0.87；类别列区分 窗/透明幕墙） |
| 窗名称 | 玻璃+气体-窗框（单/双横线） | `75系列平开窗(5Low-E+12Ar+5Low-E+12Ar+5暖边)`——括号内为玻璃系统；窗框在「窗类型N：隔热铝合金, …」段落 |
| 外门 | 户门/外门两表（构造名称） | `外门类型 \| 传热系数 \| 标准规定 \| 结论` 单表 |
| 厚度列数值 | 纯数字 | `50(65)` / `0.70[默认]`（2026-09-20：取首个数字 token，修复裙楼系列"挤塑聚苯板"层被跳过） |
| 材料表末列 | `备注`（`来源：《…》`） | `数据来源`（A#综合楼，2026-09-20 兼容；无 `来源：` 前缀时整格作规范依据） |
| 外窗命名 | `玻璃+气体-窗框[Kf=…]` | `断热铝合金窗--5中透光双银Low-E+12氩气+5透明玻璃`（双横线、框在前）与 `普通铝合金窗+12mm透明玻璃`（无分隔、首数字前为框），2026-09-20 新增 |

## PKPM 路径报告兼容性

`MaterialRecognitionPBECA.py` 本次加固的三类兼容：

| 场景 | 报告书原文 | 处理 |
|------|-----------|------|
| 内墙/分户墙/层间楼板热工表 | 公式行 `热阻 Ro=Ri+∑R+Ri=…`（两侧均室内，末格 `Ri=0.11…;Ri=0.11…`） | 识别 `R[ie]` 尾标：`Ri+∑R+Ri` → RE=RI=0.11；`Ri+∑R+Re` → 读括号后 Re 值；修复前误用默认 RE=0.05 导致 K 重算偏高 |
| 热阻对账容差 | 报告 ΣR/Ro 只给 2 位小数（如 `Ro=1.960`） | `TOL_R` 由 0.0011 放宽到 0.006（重算 1.9638 vs 报告 1.960 不再误报） |
| 表式窗外窗（38MB《公共建筑节能计算分析报告书》） | 第4章无 `构造：` 行，窗为 `外窗类型1` 小标题 + `外窗：传热系数…，外窗自身夏季/冬季太阳得热系数…，窗框系数…` + `玻璃：…玻璃遮阳系数…，玻璃可见光透射比…` 段落；判定表 `表19 外窗传热系数判定` 给 类型名→K | 新增 `build_window_v2`：SHGC 取「外窗自身」（已含框系数），SC/可见光取「玻璃」行；`表19` 兜底补充段落未覆盖的类型（如 `门透光部分类型1`）；`win_cate_from_heading` 剥掉 `类型1` 编号 |
| 非透明外门 | `非透明外门构造类型1（默认外门）：节能门1，传热系数2.00…` | 不再误判为透明窗（此前进 win_refs）；按其无热工层表的事实给出「未找到对应的热工性能判定表」告警 |

## 两个解析器说明

| 解析器 | 适用报告 | 依赖 | 输出差异 |
|--------|---------|------|---------|
| `MaterialRecognitionPBECA.py` | PKPM-PBECA《公共建筑节能计算分析报告书 / 规定性指标计算报告书》(.doc/.docx/.rtf) | **默认纯 Python**（zipfile + ElementTree，复用 `references/docx_parse.py`）；`.doc/.rtf` 仅需 Word 做一次转 .docx；`--backend word` 可强制回退 Word COM | struct + windows（无 doors） |
| `MaterialRecognitionBEC.py` | BECS / 斯维尔《建筑节能设计报告书》(.docx；斯维尔软件生成的报告) | 纯 Python（zipfile + ElementTree，无 Word） | struct + windows + doors |

## 类别映射（cateName 重命名，仅 BECS 路径）

映射定义在 `scripts/MaterialRecognitionBEC.py` 的 `CATE_RENAME_MAP`，改名称只需改该字典：

| 原类别 | 映射后 |
|--------|--------|
| 屋面 | 屋面主体层 |
| 外墙 | 填充墙 |
| 楼梯间隔墙 | 内墙填充墙 |
| 楼板 | 层间楼板 |

## 获取和设置材料
| Command Value | 功能描述 |
| :--- | :--- |
| `GetAndSetMaterial` | 获取和设置材料，必须加载了bdls，且有单栋建筑，必须在JSON文件正确生成之后。
---

## 注意事项

- 报告类型识别优先级：`.rtf` 扩展名 > 内容 PKPM 特征 > 内容 BECS/斯维尔 特征 > 默认 BECS。识别结果会打印 `[识别] 报告类型=...`，如与实际不符可用 `--force-pbeca` / `--force-bec` 纠正。
- `.doc/.rtf` 的嗅探先读文档开头 60000 字符（`SNIFF_HEAD_LIMIT`），读不到特征再退回全文，兼顾速度与识别率。注意 `Range` 上界必须 `<= doc.Content.End`，否则 Word 抛「数值超出范围」(COM -2146823680)。
- 缓存目录 `%LOCALAPPDATA%\Galp\docx_cache` 会随不同报告书累积，可整目录删除；删除后下次自动重建（只是要重新付一次 Word 转换）。加 `--no-docx-cache` 可单次绕过。
- `MaterialRecognitionPBECA.py` 单独使用时也支持 `--backend {auto,docx,word}`：`auto` 按扩展名选（`.docx`→纯 Python，其余→Word COM），`docx` 强制纯 Python（输入须为 `.docx`），`word` 强制 Word COM。
- BECS 路径纯 Python 解析 docx（zipfile + ElementTree），不依赖 Word COM / Office；PKPM 路径**改造后同样默认纯 Python**，仅 `.doc/.rtf` 需要 Word 做一次转 .docx（带缓存），`--backend word` 可强制回到 Word COM 直读。
- 输出 JSON 为 ANSI(GBK) 编码、CRLF 换行，标准 JSON（无注释，同级最后一个节点不带逗号）。BECS 路径的差异报表/备份读取为编码自适应（UTF-8→GBK 回退），两种输出变体均兼容。
- 重复运行：若 BECS 当前输出已含映射后类别（如"填充墙"），说明基线可能已被改过，需用历史备份回滚后再对比；脚本会打印告警。
- **[2026-09-20] 自动解释器**：`.doc/.rtf` 需要 Word COM（win32com）。若当前 python 无 win32com（如系统 python 3.13），调度脚本会自动改用 系统 Python（`sys.executable`）重启自身；环境变量 `MH_NO_VENV_RELAUNCH=1` 可关闭。`.docx` 全程零 Word，不需要此切换。
- **[2026-09-20] 批量模式**：`--batch` 遍历目录内全部报告书输出到 `_test_out\`；已存在产物跳过（`--force` 重做）；批量固定不写 Galp。适合回归测试与批量入库。
- **[2026-09-20] gen_mat3 幂等**：`patch_gen_mat_script` 在 gen_mat3.py 已含 CATE_RENAME 注入且 mtime 不早于 gen_mat2.py 时跳过重新生成；需强制刷新时删除 gen_mat3.py 即可。
- 报错转成中文转述：缺文件时提示"缺少必需文件"并列出缺失路径；gen_mat2.py 锚点不匹配时提示"gen_mat2.py 可能已被改动"；不支持的报告书格式会列出支持的扩展名。
- 工作目录写入：BECS 路径会在 work_dir 生成 gen_mat3.py、备份 json 及输出副本，属正常行为；若 work_dir 位于 Program Files 等安装目录（`references/*.py` 常带只读属性），`MaterialRecognitionBEC.py` 与 `gen_mat2.py` 写盘前会自动清除只读属性。
- BECS 路径构造表中非材料层行（如 `考虑热桥后K=…`、`修正后K, D`）会被自动跳过并在结尾打印 `[warn]` 清单，便于核对。
- **列号取「行内 `w:tc` 的序号」，不按 `gridSpan` 累加**。Word COM 的 `Cell.ColumnIndex`
  就是行内序号；若按 gridSpan 累加，「修正系数α(gridSpan=2)」之后的列会整体右移一位，
  导致 `parse_basis_table` 的 `parts` / `cri` 列错位（实测 28 表中 15 表出错，
  且单元格总数校验**发现不了**这个错，必须逐格比对）。
- **单元格文本必须用本模块的 `clean_cell`**（保留 `\n` 多行），不能用
  `docx_parse.table_grid` 自带的有损清洗（它把 `\r` 换成空格、吞掉 `\x0b`）。
  - **已知是 PKPM 报告书就加 `--force-pbeca`**（BECS 就加 `--force-bec`），跳过嗅探。
- **优先在 `python_executor` 里 import 调用 `dispatch()`**，不要用 shell 起新 python 进程：
  可省掉解释器启动 + win32com import（~1.5s），并能在会话内复用已 import 的模块。
  ```python
  import sys; sys.path.insert(0, r"<skill>/references/materialhandle-tools/scripts")
  from MaterialRecognitionDispatcher import dispatch
  dispatch(report=r"<报告书路径>", force="pbeca")   # galp=True 默认同步到 Galp
  ```
- **有 `.docx` 就别喂 `.doc`**：`.docx` 全程零 Word。注意同名 `.doc` 与 `.docx` 可能不是
  同一版本（本例 .doc 28 表 / .docx 26 表），要以用户指定的那份为准。
- `esab_shim.utils.link_office` 在 shell 与 `python_executor` 中均不可用，
  `[warn] 回退 win32com` 属正常现象，Word 冷启动无法靠它省掉——所以才用缓存绕过 Word。
