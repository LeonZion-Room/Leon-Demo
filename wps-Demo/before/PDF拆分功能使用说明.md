# PDF拆分功能使用说明

## 功能概述

`pdf_split` 函数是一个强大的PDF拆分工具，支持将PDF文件按指定页码拆分为多个独立的PDF文件。该功能集成在 `pdf_fc.py` 文件中，提供了命令行和GUI两种使用方式。

## 主要特性

- ✅ **灵活的拆分方式**: 支持按页码指定拆分点
- ✅ **GUI界面**: 提供可视化的PDF预览和拆分操作
- ✅ **自定义输出**: 支持自定义输出文件夹和文件名
- ✅ **智能建议**: 根据PDF页数自动建议拆分策略
- ✅ **批量处理**: 支持批量拆分多个PDF文件
- ✅ **错误处理**: 完善的错误检查和异常处理
- ✅ **实时预览**: GUI模式下可预览PDF内容和拆分点

## 函数签名

```python
def pdf_split(input_pdf_path, split_points=None, output_folder=None, custom_names=None):
    """
    PDF拆分功能：将PDF文件按指定页码拆分为多个文件
    
    Args:
        input_pdf_path (str): 输入PDF文件的路径
        split_points (list): 拆分点页码列表，例如 [3, 7, 10] 表示在第3、7、10页后拆分
                           如果为None，则弹出GUI界面让用户选择拆分点
        output_folder (str): 输出文件夹路径，如果为None则使用输入文件所在目录
        custom_names (list): 自定义输出文件名列表，如果为None则使用默认命名
        
    Returns:
        list: 输出文件路径列表，如果拆分失败则返回None
    """
```

## 使用示例

### 1. 基本用法

```python
from pdf_fc import pdf_split

# 在第3页和第7页后拆分
result = pdf_split("document.pdf", split_points=[3, 7])
print(f"生成了 {len(result)} 个文件")
```

### 2. 自定义输出设置

```python
# 自定义输出文件夹和文件名
result = pdf_split(
    input_pdf_path="document.pdf",
    split_points=[5, 10], 
    output_folder="./output",
    custom_names=["第一部分.pdf", "第二部分.pdf", "第三部分.pdf"]
)
```

### 3. GUI界面模式

```python
# 不指定拆分点，启动GUI界面
result = pdf_split("document.pdf")
```

### 4. 批量拆分

```python
pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
for pdf_file in pdf_files:
    result = pdf_split(pdf_file, split_points=[5, 10, 15])
```

### 5. 智能拆分策略

```python
import fitz

def smart_split(pdf_file):
    # 获取PDF页数
    doc = fitz.open(pdf_file)
    total_pages = len(doc)
    doc.close()
    
    # 根据页数制定拆分策略
    if total_pages <= 5:
        split_points = [total_pages // 2] if total_pages > 2 else []
    elif total_pages <= 20:
        split_points = [total_pages // 3, 2 * total_pages // 3]
    else:
        split_points = list(range(10, total_pages, 10))
    
    return pdf_split(pdf_file, split_points=split_points)
```

## GUI界面使用指南

当调用 `pdf_split()` 函数且不指定 `split_points` 参数时，会自动启动GUI界面：

### 界面功能

1. **PDF预览区域**
   - 显示当前页面的PDF内容
   - 支持页面导航（上一页/下一页）
   - 拆分点会用红色标记显示

2. **页面导航**
   - "上一页" / "下一页" 按钮
   - 当前页码显示

3. **拆分控制**
   - "设为拆分点": 在当前页设置拆分点
   - "清除拆分点": 清除所有拆分点
   - "智能建议": 根据PDF页数自动建议拆分点

4. **信息显示**
   - 显示当前拆分点列表
   - 显示预计生成的文件数量

5. **操作按钮**
   - "开始拆分": 执行拆分操作
   - "取消": 关闭界面

### 操作步骤

1. 启动GUI界面：`pdf_split("your_file.pdf")`
2. 使用导航按钮浏览PDF页面
3. 在需要拆分的页面点击"设为拆分点"
4. 或点击"智能建议"获取自动建议
5. 确认拆分点后，点击"开始拆分"
6. 等待拆分完成，查看生成的文件

## 输出文件命名规则

### 默认命名

- 格式：`原文件名_part1.pdf`, `原文件名_part2.pdf`, ...
- 示例：`document.pdf` → `document_part1.pdf`, `document_part2.pdf`

### 自定义命名

```python
custom_names = ["第一章.pdf", "第二章.pdf", "第三章.pdf"]
result = pdf_split("book.pdf", split_points=[10, 20], custom_names=custom_names)
```

## 错误处理

函数包含完善的错误处理机制：

- **FileNotFoundError**: 输入文件不存在
- **ValueError**: 文件格式不正确或拆分点无效
- **Exception**: 其他拆分过程中的错误

```python
try:
    result = pdf_split("document.pdf", split_points=[3, 7])
    if result:
        print("拆分成功!")
    else:
        print("拆分失败")
except FileNotFoundError:
    print("文件不存在")
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"拆分失败: {e}")
```

## 性能优化建议

1. **大文件处理**: 对于大型PDF文件，建议分批处理
2. **内存管理**: 函数会自动管理PDF文档的打开和关闭
3. **输出路径**: 确保输出文件夹有足够的磁盘空间
4. **拆分策略**: 合理设置拆分点，避免生成过多小文件

## 依赖要求

- `PyMuPDF (fitz)`: PDF处理
- `tkinter`: GUI界面
- `matplotlib`: PDF预览显示
- `PIL (Pillow)`: 图像处理
- `os`: 文件系统操作

## 常见问题

### Q: 如何处理加密的PDF文件？
A: 当前版本不支持加密PDF，请先解密后再使用。

### Q: 拆分后的文件质量如何？
A: 拆分是直接复制页面，不会损失质量。

### Q: 可以拆分扫描版PDF吗？
A: 可以，函数支持所有类型的PDF文件。

### Q: 如何批量拆分多个文件？
A: 参考示例代码中的批量处理部分。

## 更新日志

- **v1.0**: 初始版本，支持基本拆分功能
- **v1.1**: 添加GUI界面和智能建议
- **v1.2**: 优化错误处理和性能

## 技术支持

如有问题或建议，请查看示例代码或联系开发团队。