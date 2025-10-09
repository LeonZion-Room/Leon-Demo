# PDF拆分GUI功能使用说明

## 🖥️ GUI界面概述

PDF拆分功能提供了两种GUI界面：

1. **内置GUI界面** - 通过 `pdf_split()` 函数自动启动
2. **完整GUI应用** - 独立的图形界面程序

## 📋 方式一：内置GUI界面

### 启动方法

```python
from pdf_fc import pdf_split

# 不指定split_points参数，自动启动GUI
result = pdf_split("your_file.pdf")
```

### 界面功能

#### 1. PDF预览区域
- 📖 **页面显示**: 实时显示PDF页面内容
- 🔍 **缩放优化**: 自动调整页面大小适应窗口
- 📍 **拆分标记**: 拆分点用红色标记显示

#### 2. 页面导航
- ⬅️ **上一页**: 浏览到前一页
- ➡️ **下一页**: 浏览到后一页  
- 📊 **页码显示**: 显示当前页码和总页数

#### 3. 拆分控制
- ✅ **设为拆分点**: 在当前页设置拆分点
- 🗑️ **清除拆分点**: 清除所有已设置的拆分点
- 🧠 **智能建议**: 根据PDF页数自动建议拆分策略

#### 4. 信息显示
- 📋 **拆分点列表**: 显示当前所有拆分点
- 📊 **文件预览**: 显示将要生成的文件数量

#### 5. 操作按钮
- 🚀 **开始拆分**: 执行PDF拆分操作
- ❌ **取消**: 关闭界面，取消操作

### 使用步骤

```python
# 示例代码
from pdf_fc import pdf_split

# 1. 启动GUI界面
result = pdf_split("测试材料/长图(编辑后).pdf")

# 2. 在GUI中进行以下操作：
#    - 使用上一页/下一页浏览PDF
#    - 在需要拆分的页面点击"设为拆分点"
#    - 或点击"智能建议"获取自动建议
#    - 点击"开始拆分"完成操作

# 3. 获取结果
if result:
    print(f"拆分成功，生成了 {len(result)} 个文件")
    for file in result:
        print(f"  - {file}")
else:
    print("拆分失败或用户取消")
```

## 🖼️ 方式二：完整GUI应用

### 启动方法

```bash
python pdf_split_gui_demo.py
```

### 界面功能

#### 1. 文件选择区域
- 📁 **浏览按钮**: 选择要拆分的PDF文件
- 📄 **文件显示**: 显示当前选择的文件名

#### 2. 拆分方式选择
- 🖥️ **可视化界面模式**: 启动内置GUI进行可视化拆分
- ✏️ **手动指定模式**: 直接输入拆分页码
- 🧠 **智能拆分模式**: 自动计算最佳拆分点

#### 3. 输出设置
- 📂 **输出文件夹**: 选择输出文件的保存位置
- 🏷️ **自定义文件名**: 设置输出文件的自定义名称

#### 4. 操作按钮
- 🚀 **开始拆分**: 执行拆分操作
- 🧪 **使用测试文件**: 快速选择测试PDF文件
- ❓ **使用帮助**: 显示详细的使用说明

### 使用步骤

1. **启动程序**
   ```bash
   python pdf_split_gui_demo.py
   ```

2. **选择文件**
   - 点击"浏览"按钮选择PDF文件
   - 或点击"使用测试文件"快速选择

3. **选择拆分方式**
   - **可视化模式**: 推荐，提供PDF预览
   - **手动模式**: 输入页码，如 "3, 7, 10"
   - **智能模式**: 自动计算拆分点

4. **设置输出**
   - 选择输出文件夹（可选）
   - 设置自定义文件名（可选）

5. **开始拆分**
   - 点击"开始拆分"按钮
   - 等待处理完成

## 🎯 智能拆分策略

### 策略说明

智能拆分会根据PDF页数自动选择最佳策略：

- **小文档 (≤5页)**: 对半拆分
- **中等文档 (6-20页)**: 三等分
- **大文档 (>20页)**: 每10页拆分一次

### 示例

```python
# 智能拆分示例
def smart_split_example():
    import fitz
    from pdf_fc import pdf_split
    
    pdf_file = "document.pdf"
    
    # 获取页数
    doc = fitz.open(pdf_file)
    total_pages = len(doc)
    doc.close()
    
    print(f"PDF总页数: {total_pages}")
    
    # 计算智能拆分点
    if total_pages <= 5:
        split_points = [total_pages // 2] if total_pages > 2 else []
        strategy = "小文档策略: 对半拆分"
    elif total_pages <= 20:
        split_points = [total_pages // 3, 2 * total_pages // 3]
        strategy = "中等文档策略: 三等分"
    else:
        split_points = list(range(10, total_pages, 10))
        strategy = "大文档策略: 每10页拆分"
    
    print(f"策略: {strategy}")
    print(f"拆分点: {split_points}")
    
    # 执行拆分
    result = pdf_split(pdf_file, split_points=split_points)
    return result
```

## 🔧 高级功能

### 1. 自定义输出设置

```python
# 自定义输出文件夹和文件名
result = pdf_split(
    input_pdf_path="document.pdf",
    split_points=None,  # 启动GUI
    output_folder="./输出文件夹",
    custom_names=["第一章.pdf", "第二章.pdf", "第三章.pdf"]
)
```

### 2. 批量处理

```python
# 批量拆分多个PDF
pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

for pdf_file in pdf_files:
    print(f"正在处理: {pdf_file}")
    result = pdf_split(pdf_file)  # 每个文件都会弹出GUI
    if result:
        print(f"  成功生成 {len(result)} 个文件")
```

### 3. 错误处理

```python
try:
    result = pdf_split("document.pdf")
    if result:
        print("拆分成功!")
    else:
        print("用户取消或拆分失败")
except FileNotFoundError:
    print("文件不存在")
except Exception as e:
    print(f"拆分出错: {e}")
```

## 🚀 快速开始

### 最简单的使用方法

```python
# 1. 导入函数
from pdf_fc import pdf_split

# 2. 启动GUI拆分
result = pdf_split("your_file.pdf")

# 3. 检查结果
if result:
    print(f"成功生成 {len(result)} 个文件")
```

### 使用测试文件

```python
# 使用项目中的测试文件
test_files = [
    "测试材料/长图(编辑后).pdf",
    "测试材料/有字pdf.pdf",
    "测试材料/无字pdf.pdf"
]

for test_file in test_files:
    if os.path.exists(test_file):
        result = pdf_split(test_file)
        break
```

## 📱 界面截图说明

### 内置GUI界面
```
┌─────────────────────────────────────────┐
│              PDF拆分预览                 │
│  文件: document.pdf | 总页数: 10        │
├─────────────────────────────────────────┤
│                                         │
│           [PDF页面预览区域]              │
│                                         │
│              📍 拆分点                   │
├─────────────────────────────────────────┤
│ [上一页] [下一页]    第 3 / 10 页       │
├─────────────────────────────────────────┤
│ [设为拆分点] [清除拆分点] [智能建议]     │
│                    拆分点: [3,7] | 3个文件│
├─────────────────────────────────────────┤
│ [开始拆分]                    [取消]    │
└─────────────────────────────────────────┘
```

### 完整GUI应用
```
┌─────────────────────────────────────────┐
│            PDF拆分工具                   │
├─────────────────────────────────────────┤
│ 选择PDF文件                             │
│ document.pdf                  [浏览]    │
├─────────────────────────────────────────┤
│ 拆分方式                               │
│ ○ 可视化界面模式 (推荐)                 │
│ ○ 手动指定页码模式                     │
│ ○ 智能拆分模式                         │
├─────────────────────────────────────────┤
│ 输出设置                               │
│ 输出文件夹: [选择文件夹]                │
│ ☐ 使用自定义文件名                     │
├─────────────────────────────────────────┤
│ [开始拆分] [使用测试文件]    [使用帮助] │
└─────────────────────────────────────────┘
```

## ❓ 常见问题

### Q: GUI界面没有弹出怎么办？
A: 检查Python环境和tkinter是否正确安装，或者使用手动模式。

### Q: 如何预览拆分效果？
A: 使用可视化界面模式，可以实时预览PDF内容和拆分点。

### Q: 可以同时设置多个拆分点吗？
A: 可以，在GUI中多次点击"设为拆分点"即可。

### Q: 智能建议的拆分点不满意怎么办？
A: 可以清除后手动设置，或者使用手动指定模式。

## 🎉 总结

PDF拆分GUI功能提供了直观、易用的图形界面，支持：

- ✅ 实时PDF预览
- ✅ 可视化拆分点设置  
- ✅ 智能拆分建议
- ✅ 自定义输出设置
- ✅ 完整的错误处理
- ✅ 友好的用户体验

无论是简单的文档拆分还是复杂的批量处理，GUI界面都能提供便捷的操作体验。