"""
简历解析模块
负责从 PDF 文件中提取文本内容
"""

import io

import pdfplumber
from pathlib import Path


def extract_text_from_pdf(file_path: str | Path) -> str:
    """
    从 PDF 文件中提取文本

    Args:
        file_path: PDF 文件路径

    Returns:
        提取出的文本内容

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件无法解析或内容为空
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"找不到文件: {file_path}")

    text_parts = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise ValueError(f"PDF 解析失败: {e}")

    full_text = "\n\n".join(text_parts).strip()

    if not full_text:
        raise ValueError("未能从 PDF 中提取到文本，请检查文件是否为扫描件或图片 PDF")

    return full_text


def extract_text_from_bytes(file_bytes: bytes) -> str:
    """
    从 PDF 二进制数据中直接提取文本

    Args:
        file_bytes: PDF 文件二进制内容

    Returns:
        提取出的文本内容
    """
    text_parts = []

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise ValueError(f"PDF 解析失败: {e}")

    full_text = "\n\n".join(text_parts).strip()

    if not full_text:
        raise ValueError("未能从 PDF 中提取到文本，请检查文件是否为扫描件或图片 PDF")

    return full_text


