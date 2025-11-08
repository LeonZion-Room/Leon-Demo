import os
from typing import Callable, Iterable, List, Optional


def _safe_cb(cb: Optional[Callable[[int, str], None]], pct: int, msg: str) -> None:
    if cb:
        try:
            cb(int(pct), msg)
        except Exception:
            pass


def pdf2docx(pdf_path: str, output_path: Optional[str] = None, progress_cb: Optional[Callable[[int, str], None]] = None) -> str:
    """使用 Windows Word 自动化将 PDF 转换为 DOCX。

    说明：
    - 需要本机安装 Microsoft Word。
    - 依赖 comtypes 库与 Word 的 COM 接口交互。

    参数：
    - pdf_path: 输入 PDF 文件路径
    - output_path: 输出 DOCX 文件路径（不指定则与输入同目录同名）
    - progress_cb: 进度回调 (pct:int, msg:str)
    """

    _safe_cb(progress_cb, 0, "开始准备")

    if not pdf_path:
        raise ValueError("pdf_path 不能为空")
    pdf_path = os.path.abspath(pdf_path)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")

    if output_path is None:
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(os.path.dirname(pdf_path), f"{base}.docx")
    else:
        output_path = os.path.abspath(output_path)
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    _safe_cb(progress_cb, 10, "检查环境")

    try:
        from comtypes.client import EnsureDispatch
    except Exception as e:
        # 自动尝试安装 comtypes 到当前解释器
        _safe_cb(progress_cb, 15, "缺少 comtypes，正在自动安装…")
        try:
            import subprocess, sys
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "comtypes",
                "-i", "https://mirrors.aliyun.com/pypi/simple/",
            ])
            from comtypes.client import EnsureDispatch  # 再次尝试
        except Exception as e2:
            raise RuntimeError(
                "缺少 comtypes 库，请安装: .venv\\Scripts\\pip install comtypes -i https://mirrors.aliyun.com/pypi/simple/"
            ) from e2

    _safe_cb(progress_cb, 20, "启动 Word")

    word = EnsureDispatch('Word.Application')
    word.Visible = False

    doc = None
    try:
        _safe_cb(progress_cb, 40, "打开 PDF")
        # 打开 PDF（Word 会进行内部转换）
        doc = word.Documents.Open(pdf_path, ConfirmConversions=False, ReadOnly=True)

        _safe_cb(progress_cb, 70, "保存为 DOCX")
        # 常量：wdFormatXMLDocument = 12
        doc.SaveAs(output_path, FileFormat=12)

        _safe_cb(progress_cb, 90, "收尾")
        doc.Close(False)
        doc = None
        return output_path
    except Exception as e:
        raise RuntimeError(f"Word 转换失败: {e}")
    finally:
        try:
            if doc is not None:
                doc.Close(False)
        except Exception:
            pass
        try:
            word.Quit()
        except Exception:
            pass


def pdf2docx_batch(folder_path: str, output_dir: Optional[str] = None, progress_cb: Optional[Callable[[int, str], None]] = None) -> List[str]:
    """批量转换文件夹中的 PDF 为 DOCX。
    - output_dir 不指定时，输出到各自 PDF 所在目录。
    - 进度为整体估算；每个文件内部仍调用单文件的进度。
    """

    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")

    pdfs = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    total = len(pdfs)
    if total == 0:
        _safe_cb(progress_cb, 100, "没有 PDF 文件")
        return []

    results: List[str] = []
    for i, pdf in enumerate(pdfs, start=1):
        base = os.path.splitext(os.path.basename(pdf))[0]
        out = os.path.join(output_dir or os.path.dirname(pdf), f"{base}.docx")
        _safe_cb(progress_cb, int((i - 1) * 100 / total), f"转换: {os.path.basename(pdf)}")
        res = pdf2docx(pdf, out, progress_cb=progress_cb)
        results.append(res)
        _safe_cb(progress_cb, int(i * 100 / total), f"完成: {os.path.basename(pdf)}")
    return results