"""
简历导出模块
负责把优化后的简历文本导出为 Word 文档
"""

import re
from io import BytesIO

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


def extract_optimized_resume(analysis_text: str) -> str:
    """
    从 AI 分析结果中提取优化后的简历内容

    Args:
        analysis_text: AI 返回的完整分析文本

    Returns:
        优化后的简历文本
    """
    # 尝试匹配 ===OPTIMIZED_RESUME_START=== 标记
    match = re.search(
        r"===OPTIMIZED_RESUME_START===(.*?)===OPTIMIZED_RESUME_END===",
        analysis_text,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    # 兼容旧格式：匹配 "## 优化后的简历" 标题后的内容
    match = re.search(r"##\s*优化后的简历\s*\n(.*)", analysis_text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 如果没找到，返回空字符串
    return ""


def create_resume_docx(resume_text: str) -> BytesIO:
    """
    把简历文本转换为 Word 文档

    Args:
        resume_text: 简历文本内容

    Returns:
        Word 文档的字节流
    """
    doc = Document()

    # 设置默认字体
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(10.5)
    style._element.rPr.rFonts.set("w:eastAsia", "宋体")

    # 逐行写入
    for line in resume_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # 判断是否是标题行（比如"教育背景"、"工作经历"等）
        section_titles = [
            "个人信息",
            "求职意向",
            "教育背景",
            "工作经历",
            "项目经历",
            "项目经验",
            "技能",
            "技能证书",
            "专业技能",
            "自我评价",
            "荣誉证书",
        ]

        is_title = any(
            line == title or line.startswith(title + " ") or line.startswith(title + "|")
            for title in section_titles
        )

        if is_title or line.endswith("：") or line.endswith(":"):
            # 标题样式
            p = doc.add_paragraph(line)
            run = p.runs[0]
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0, 0, 0)
            p.space_before = Pt(12)
            p.space_after = Pt(6)
        else:
            # 正文
            p = doc.add_paragraph(line)
            p.space_after = Pt(3)

    # 保存到字节流
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def export_optimized_resume_to_docx(analysis_text: str) -> tuple[BytesIO, str]:
    """
    从分析结果中提取优化后的简历，并生成 Word 文档

    Args:
        analysis_text: AI 返回的完整分析文本

    Returns:
        (Word 文档字节流, 优化后的简历文本)
    """
    resume_text = extract_optimized_resume(analysis_text)
    if not resume_text:
        raise ValueError("未能从分析结果中提取到优化后的简历")

    docx_buffer = create_resume_docx(resume_text)
    return docx_buffer, resume_text
