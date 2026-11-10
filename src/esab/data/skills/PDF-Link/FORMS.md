

# 填写 PDF 表单

**按顺序完成下面的步骤，不要跳过。直接动手写代码很容易把坐标系搞错。**

依赖（按需通过 shell 运行 `pip install ...`）：

```
pypdf pdfplumber pypdfium2 Pillow
```

调用规则：本目录下的 `scripts/` 内是所有工具脚本。从这个 skill 的根目录运行它们：

```
python scripts/<script_name>.py <args...>
```

---

## Step 0：判断是否是"可填写"的 PDF

PDF 有两种表单：

- **fillable**：PDF 自身带 AcroForm 字段（点击空白处会出现输入框）。改 PDF 内部的字段值即可。
- **non-fillable**：表格是画上去的（线、文字、方框就是普通图形），需要把文字"叠加"到正确的位置上去。

先跑这个脚本判断：

```
python scripts/check_fillable_fields.py <file.pdf>
```

根据输出走 **A. Fillable** 或 **B. Non-fillable** 分支。

---

## A. Fillable 分支

### A.1 导出字段清单

```
python scripts/extract_form_field_info.py <input.pdf> <field_info.json>
```

JSON 结构：

```json
[
  {
    "field_id": "<unique id>",
    "page": 1,
    "rect": [left, bottom, right, top],
    "type": "text"
  },
  {
    "field_id": "...",
    "type": "checkbox",
    "checked_value": "/Yes",
    "unchecked_value": "/Off"
  },
  {
    "field_id": "...",
    "type": "radio_group",
    "radio_options": [
      {"value": "/Option1", "rect": [...]}
    ]
  },
  {
    "field_id": "...",
    "type": "choice",
    "choice_options": [
      {"value": "v1", "text": "显示文本"}
    ]
  }
]
```

坐标系：PDF 坐标，原点在页面左下角，y 向上为正。

### A.2 渲染每一页 PNG 帮助判断每个字段的含义

```
python scripts/convert_pdf_to_images.py <input.pdf> <output_dir>
```

看着图，给每个字段决定一个值。把 PDF 的 `rect`（左下原点）换成图像像素时记得 y 轴翻转。

### A.3 写 `field_values.json`

```json
[
  {
    "field_id": "last_name",
    "description": "用户姓",
    "page": 1,
    "value": "Simpson"
  },
  {
    "field_id": "Checkbox12",
    "description": "年满 18 岁",
    "page": 1,
    "value": "/On"
  }
]
```

复选框的 `value` 用 `checked_value` / `unchecked_value`；单选用 `radio_options` 里的 `value`；多选用 `choice_options` 里的 `value`。

### A.4 写回 PDF

```
python scripts/fill_fillable_fields.py <input.pdf> <field_values.json> <output.pdf>
```

脚本会自动校验 `field_id`、`page`、`value` 是否合法；如果报 ERROR，按提示改 JSON 再跑一次。

---

## B. Non-fillable 分支

这种情况要自己算出每个字段该写在哪个矩形里，然后把文字作为 FreeText 注释叠到 PDF 上。

### B.1 先尝试结构抽取

```
python scripts/extract_form_structure.py <input.pdf> <form_structure.json>
```

输出包含：
- `labels`：页面里每个词的精确坐标
- `lines`：横线（一般是行边界）
- `checkboxes`：尺寸接近正方形的小矩形（候选复选框）
- `row_boundaries`：用横线推出的行上下界

**判断走哪种方法**：
- 如果 `labels` 里有有意义的文字（能看出"姓名"、"地址"这种标签）→ **方法 A：结构法**
- 如果 labels 几乎为空（数字版扫描件、文字全是 `(cid:X)` 这种乱码）→ **方法 B：视觉法**

注意：本 skill 不覆盖扫描件的文字识别。若是纯扫描件，本工作流可以为方框/横线提供基础布局，但字段标签的含义需要用别的能力（如视觉模型）来判断。

---

### 方法 A：基于结构的坐标（推荐）

#### A.a 分析结构

读 `form_structure.json`，理出：
1. **标签分组**：相邻、`top` 相近的 word 通常是同一个标签（如 "Last" + "Name"）
2. **行结构**：`top` 相近的 labels 在同一行
3. **字段填写区**：从标签右侧开始（`x0 ≈ label.x1 + 间距`）
4. **复选框**：直接用 `checkboxes` 里的矩形

**坐标系**：pdfplumber 的坐标 `top` 是从页面顶部往下增长（注意和 pypdf 的 PDF 原生坐标 y 轴方向相反）。

#### A.b 处理结构遗漏的元素

`extract_form_structure.py` 不一定能识别所有控件：
- **圆形复选框**：脚本只看正方形小矩形
- **复杂图形 / 浅色控件**：可能被忽略
- **手写线条 / 非标准控件**：可能识别错位

如果有控件没出现在 `form_structure.json`，对这些元素改用下面的视觉法（混合模式见末尾）。

#### A.c 写 `fields.json`（PDF 坐标）

文本字段：
- entry x0 = label x1 + 5
- entry x1 = 下一个标签的 x0 或 行右边界
- entry top = 标签 top
- entry bottom = 下方行边界 或 label bottom + row_height

复选框：直接用 `checkboxes` 里的坐标作为 entry_bounding_box。

用 `pdf_width`/`pdf_height` 标记是 PDF 坐标：

```json
{
  "pages": [
    {"page_number": 1, "pdf_width": 612, "pdf_height": 792}
  ],
  "form_fields": [
    {
      "page_number": 1,
      "description": "姓名输入框",
      "field_label": "姓名",
      "label_bounding_box": [43, 63, 87, 73],
      "entry_bounding_box": [92, 63, 260, 79],
      "entry_text": {"text": "张三", "font_size": 10}
    },
    {
      "page_number": 1,
      "description": "是否本市户籍：是",
      "field_label": "是",
      "label_bounding_box": [260, 200, 280, 210],
      "entry_bounding_box": [285, 197, 292, 205],
      "entry_text": {"text": "X"}
    }
  ]
}
```

中文字符需要选支持中文的字体（见下文"中文字体"一节）。

---

### 方法 B：视觉估计（兜底）

当 PDF 是扫描件、结构抽取拿不到有用的标签时用这种方法。

#### B.a 渲染 PDF 为 PNG

```
python scripts/convert_pdf_to_images.py <input.pdf> <images_dir>
```

默认 200 DPI，最长边压到 1000 像素以便看清版面。需要更精细时加 `--dpi 300 --max-dim 0`。

#### B.b 粗估字段位置

看每一页图，确定每个字段标签的位置、对应的填写区域（横线、方框、空白处）、复选框位置。先得到一个粗糙的像素坐标即可。

#### B.c 放大裁剪精修坐标（关键）

对每个字段，把它附近的区域裁出来放大看，确定精确的像素坐标。用 PIL 即可，**不需要 ImageMagick**：

```python
from PIL import Image

img = Image.open("images_dir/page_1.png")
# (left, upper, right, lower)
crop = img.crop((50, 120, 50 + 300, 120 + 80))
crop.save("crops/name_field.png")
```

打开 `crops/name_field.png` 看清楚后：
- 找到填写区左边界（label 结束的下一像素）
- 找到填写区右边界
- 找到填写区上下边界

把裁切局部坐标加回偏移得到整页坐标：
```
full_x = crop_x_in_image + crop_offset_x
full_y = crop_y_in_image + crop_offset_y
```

附近的字段可以一次裁一大块共享。

#### B.d 写 `fields.json`（图像坐标）

用 `image_width`/`image_height` 标记是图像坐标：

```json
{
  "pages": [
    {"page_number": 1, "image_width": 1700, "image_height": 2200}
  ],
  "form_fields": [
    {
      "page_number": 1,
      "description": "姓名输入框",
      "field_label": "姓名",
      "label_bounding_box": [120, 175, 242, 198],
      "entry_bounding_box": [255, 175, 720, 218],
      "entry_text": {"text": "张三", "font_size": 10}
    }
  ]
}
```

填充脚本会根据 PDF 真实尺寸自动换算回 PDF 坐标，y 轴翻转也由脚本处理。

---

### 混合模式：结构 + 视觉

`extract_form_structure.py` 漏掉一部分控件时：
1. 已识别字段用结构坐标
2. 漏掉的字段用方法 B 视觉裁剪定位
3. **统一坐标系**：把视觉得到的图像坐标换算为 PDF 坐标，最终 `fields.json` 用 `pdf_width`/`pdf_height`：

```
pdf_x = image_x * (pdf_width / image_width)
pdf_y = image_y * (pdf_height / image_height)
```

---

### B.X 校验坐标

写好 `fields.json` 后，**填写前先跑这一步**：

```
python scripts/check_bounding_boxes.py <fields.json>
```

它会检查：
- 不同字段的 bounding box 是否相交（相交会导致文字叠在一起）
- entry 框的高度是否能容纳给定字号

报错就回去改 `fields.json` 重跑，直到 `SUCCESS`。

可选：把方框画到页面图上人工核对：

```
python scripts/create_validation_image.py <page_number> <fields.json> <page_image.png> <validation_out.png>
```

红框是 entry，蓝框是 label。

### B.Y 写回 PDF

```
python scripts/fill_pdf_form_with_annotations.py <input.pdf> <fields.json> <output.pdf>
```

脚本会根据 `pages` 里的标记（`pdf_width` 还是 `image_width`）自动选择坐标转换。

### B.Z 渲染回图检查

```
python scripts/convert_pdf_to_images.py <output.pdf> <verify_images>
```

肉眼对比 `verify_images/` 和原图，看文字是否落在正确位置、是否越界。如果错位：
- 方法 A：确认 `fields.json` 用的是 PDF 坐标、字段标签匹配 `form_structure.json` 里的来源
- 方法 B：确认 `image_width`/`image_height` 和实际图像尺寸一致
- 混合：检查图像 → PDF 坐标换算是否正确

---

## 中文字体

`fill_pdf_form_with_annotations.py` 默认用 Arial。中文要么走 PDF 内嵌的 CJK 字体（如果原 PDF 就有），要么在 `entry_text` 里显式指定一个能渲染中文的字体名，例如：

```json
{"text": "张三", "font": "SimSun", "font_size": 10}
```

如果生成 PDF 中文显示为问号或方块，把字段值临时改为拼音先跑通流程，再回头处理字体嵌入问题——`pypdf.annotations.FreeText` 用的是 PDF 标准 14 字体名集合，要内嵌中文 TTF 通常需要改成自己用 `reportlab` 生成一个水印 PDF 再 `merge_page` 叠上去（见 SKILL.md 的"加水印"一节，把水印 PDF 当成填写文字）。

## 常见问题

- **填好的字段在 Adobe Reader 里看不到，但在浏览器或预览里能看到** —— Fillable 表单需要写入 NeedAppearances 标志。`fill_fillable_fields.py` 已经调用 `set_need_appearances_writer(True)` 解决了这点。
- **PDF 报 `PyCryptodome is required`** —— `pip install pycryptodome`。
- **`extract_form_structure.py` 跑出来 `labels` 全是 `(cid:N)`** —— PDF 用了未嵌入字体或 CID 编码，无法直接读文字。走方法 B（视觉）。
- **`check_bounding_boxes.py` 总是报相交** —— 大概率是相邻字段的 entry 框写得太宽。把它们缩小，让两个相邻字段之间至少留 2-3 像素的间隙。
