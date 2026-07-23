"""
生成示例简历 PDF
用于测试 meng 的简历解析功能
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


def generate_sample_resume():
    """生成示例简历 PDF"""
    txt_path = ROOT_DIR / "examples" / "sample_resume.txt"
    pdf_path = ROOT_DIR / "examples" / "sample_resume.pdf"

    if not txt_path.exists():
        raise FileNotFoundError(f"找不到示例简历文本: {txt_path}")

    # 读取文本内容
    resume_text = txt_path.read_text(encoding="utf-8")

    # 创建 PDF
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    # 设置中文字体（用系统自带的 simsun.ttf）
    font_name = "SimSun"
    font_paths = [
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simsun.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
    ]

    font_registered = False
    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                font_registered = True
                break
            except Exception:
                continue

    if not font_registered:
        raise RuntimeError("找不到中文字体，请确保系统有 simsun 或 msyh 字体")

    # 写入文本
    c.setFont(font_name, 12)
    margin = 50
    y_position = height - margin
    line_height = 20

    for line in resume_text.split("\n"):
        if y_position < margin:
            c.showPage()
            c.setFont(font_name, 12)
            y_position = height - margin

        c.drawString(margin, y_position, line)
        y_position -= line_height

    c.save()
    print(f"示例简历 PDF 已生成: {pdf_path}")


if __name__ == "__main__":
    generate_sample_resume()
