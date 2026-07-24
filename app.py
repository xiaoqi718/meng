"""
meng - AI 简历优化器
Streamlit 前端主程序
"""

import base64
import os
import re
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.resume_analyzer import analyze_resume
from src.resume_parser import extract_text_from_pdf

# 加载 .env 文件
load_dotenv()


def get_background_css() -> str:
    """
    读取 assets/background.* 图片并转为 base64 CSS 背景
    支持 png / jpg / jpeg / webp
    如果图片不存在，返回空字符串（使用默认背景色）
    """
    candidates = ["assets/background.png", "assets/background.jpg", "assets/background.jpeg", "assets/background.webp"]

    for candidate in candidates:
        image_path = Path(candidate)
        if not image_path.exists():
            continue

        data = image_path.read_bytes()
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"
        elif data.startswith(b"\xff\xd8"):
            mime = "image/jpeg"
        elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
            mime = "image/webp"
        else:
            continue

        encoded = base64.b64encode(data).decode()
        return f"url('data:{mime};base64,{encoded}')"

    return ""


# 页面配置
st.set_page_config(
    page_title="meng - AI 简历优化器",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

bg_image = get_background_css()

# 自定义样式：简约专业 SaaS 风格 + 背景图
st.markdown(
    f"""
    <style>
    /* 页面背景 */
    .stApp {{
        background-color: #F8FAFC;
        {"background: linear-gradient(rgba(248, 250, 252, 0.88), rgba(248, 250, 252, 0.88)), " + bg_image + " center/cover no-repeat fixed;" if bg_image else ""}
    }}

    /* 隐藏 Streamlit 底部和多余元素 */
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none !important;}}
    #MainMenu {{visibility: hidden;}}

    /* 主容器 */
    .main .block-container {{
        max-width: 960px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }}

    /* 卡片 */
    .card {{
        background: rgba(255, 255, 255, 0.96);
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 24px;
        backdrop-filter: blur(8px);
    }}

    .card-title {{
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        margin-bottom: 1rem !important;
    }}

    .card-subtitle {{
        font-size: 0.95rem;
        color: #64748B;
        line-height: 1.6;
    }}

    /* Header 区域 */
    .app-header {{
        text-align: center;
        margin-bottom: 2rem;
    }}

    .app-logo {{
        font-size: 2rem;
        font-weight: 800;
        color: #2563EB;
        letter-spacing: -1px;
        margin-bottom: 0.25rem;
    }}

    .app-title {{
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        margin-bottom: 0.5rem !important;
    }}

    .app-subtitle {{
        font-size: 1rem;
        color: #64748B;
        line-height: 1.6;
    }}

    /* 上传区 */
    .stFileUploader {{
        background: #FFFFFF;
        border: 2px dashed #CBD5E1 !important;
        border-radius: 12px;
        padding: 1.5rem;
    }}

    .stFileUploader:hover {{
        border-color: #2563EB !important;
    }}

    .stFileUploader label,
    .stFileUploader > div > div,
    .stFileUploader small {{
        color: #475569 !important;
    }}

    /* 按钮 */
    .stButton > button {{
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-size: 1rem;
        font-weight: 600;
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.15);
        transition: all 0.15s ease;
    }}

    .stButton > button:hover {{
        background-color: #1D4ED8 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }}

    .stButton > button:active {{
        transform: translateY(0);
    }}

    .stButton > button:disabled {{
        background-color: #94A3B8 !important;
    }}

    /* 评分卡片 */
    .score-card {{
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        text-align: center;
    }}

    .score-number {{
        font-size: 3rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.5rem;
    }}

    .score-label {{
        font-size: 0.9rem;
        opacity: 0.9;
    }}

    /* 标签 */
    .badge {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
    }}

    .badge-success {{ background: #D1FAE5; color: #065F46; }}
    .badge-warning {{ background: #FEF3C7; color: #92400E; }}
    .badge-danger {{ background: #FEE2E2; color: #991B1B; }}
    .badge-info {{ background: #DBEAFE; color: #1E40AF; }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 1px solid #E2E8F0;
    }}

    .stTabs [data-baseweb="tab"] {{
        padding: 12px 20px;
        font-weight: 600;
        color: #64748B;
        border-radius: 8px 8px 0 0;
    }}

    .stTabs [aria-selected="true"] {{
        color: #2563EB !important;
        background: #EFF6FF;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        font-weight: 600 !important;
        color: #0F172A !important;
        background: #F8FAFC;
        border-radius: 10px;
        padding: 14px 16px !important;
    }}

    .streamlit-expander {{
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        margin-bottom: 12px;
        background: #FFFFFF;
    }}

    /* 提示框 */
    .stAlert {{
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
    }}

    .stAlert [data-testid="stMarkdownContainer"] p {{
        color: #0F172A !important;
    }}

    /* 分隔线 */
    hr {{
        border: none !important;
        border-top: 1px solid #E2E8F0 !important;
        margin: 1.5rem 0 !important;
    }}

    /* 简历预览 */
    .resume-preview {{
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        line-height: 1.7;
        color: #0F172A;
        font-size: 0.95rem;
    }}

    .resume-preview h1,
    .resume-preview h2,
    .resume-preview h3 {{
        color: #0F172A !important;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }}

    .resume-preview p {{
        margin-bottom: 0.5rem;
    }}

    /* 小字说明 */
    .hint-text {{
        font-size: 0.85rem;
        color: #94A3B8;
        margin-top: 0.5rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_score_section(text: str) -> tuple[str, str]:
    """
    从 AI 输出中提取评分部分
    返回 (评分部分, 剩余内容)
    """
    score_match = re.search(r"#{1,3}\s*简历评分[:：]\s*(\d{1,3}/100)", text)
    if score_match:
        score = score_match.group(1)
        rest = text[score_match.end():].strip()
        return score, rest
    return "", text


def split_analysis_result(text: str) -> tuple[str, str]:
    """
    把 AI 输出分成：分析部分 和 优化后的简历部分
    """
    # 新格式：用标记包裹
    match = re.search(
        r"===OPTIMIZED_RESUME_START===(.*?)===OPTIMIZED_RESUME_END===",
        text,
        re.DOTALL,
    )
    if match:
        analysis_part = text[: match.start()].strip()
        resume_part = match.group(1).strip()
        return analysis_part, resume_part

    # 兼容旧格式
    match = re.search(r"##\s*优化后的简历\s*\n(.*)", text, re.DOTALL)
    if match:
        analysis_part = text[: match.start()].strip()
        resume_part = match.group(1).strip()
        return analysis_part, resume_part

    return text, ""


def get_api_key() -> str:
    """
    获取 DeepSeek API Key
    线上优先从 Streamlit Secrets 读取，本地从 .env 环境变量读取
    """
    # 线上环境：Streamlit Cloud Secrets
    try:
        return st.secrets["DEEPSEEK_API_KEY"]
    except (KeyError, AttributeError):
        pass

    # 本地环境：.env 文件
    return os.getenv("DEEPSEEK_API_KEY", "")


def get_score_badge(score_num: int) -> str:
    """根据分数返回评级标签 HTML"""
    if score_num >= 85:
        return '<span class="badge badge-success">钻石级</span>'
    elif score_num >= 70:
        return '<span class="badge badge-info">黄金级</span>'
    elif score_num >= 60:
        return '<span class="badge badge-warning">白银级</span>'
    else:
        return '<span class="badge badge-danger">青铜级</span>'


def render_header():
    """渲染顶部标题"""
    st.markdown(
        '''
        <div class="app-header">
            <div class="app-logo">meng</div>
            <div class="app-title">AI 简历优化器</div>
            <div class="app-subtitle">
                上传简历 · AI 诊断问题 · 输出优化版本
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_upload_card():
    """渲染上传卡片"""
    st.markdown('<div class="card">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            '''
            <div class="card-title">📄 上传简历</div>
            <div class="card-subtitle">
                支持 PDF 格式。AI 会分析你的简历，指出问题并直接输出一份优化后的完整版本。
            </div>
            <ul style="color: #64748B; font-size: 0.9rem; line-height: 1.8; margin-top: 1rem; padding-left: 1.2rem;">
                <li>AI 诊断简历问题</li>
                <li>输出标准结构优化版</li>
                <li>保留真实信息，不编造经历</li>
            </ul>
            ''',
            unsafe_allow_html=True,
        )

    with col2:
        uploaded_file = st.file_uploader(
            "拖拽或点击上传 PDF 简历",
            type=["pdf"],
            help="请上传文字版 PDF，扫描件/图片可能无法识别",
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            st.success(f"已上传：**{uploaded_file.name}**")
        else:
            st.markdown('<div class="hint-text">未选择文件</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    return uploaded_file


def render_analyze_button(uploaded_file):
    """渲染分析按钮"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        disabled = uploaded_file is None
        button_label = "开始分析" if uploaded_file else "请先上传简历"
        return st.button(
            button_label,
            type="primary",
            disabled=disabled,
            use_container_width=True,
        )


def render_progress(step: int):
    """渲染步骤进度 1=读取 2=分析 3=完成"""
    steps = ["读取 PDF 内容", "AI 审阅简历", "生成优化版本"]
    progress_value = step / len(steps)
    current_label = steps[step - 1] if 1 <= step <= len(steps) else "完成"
    st.progress(progress_value, text=f"步骤 {step}/{len(steps)}：{current_label}")


def render_score_section(score: str, analysis_text: str):
    """渲染评分和摘要"""
    try:
        score_num = int(score.split("/")[0])
    except ValueError:
        score_num = 0

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown(
            f'''
            <div class="score-card">
                <div class="score-number">{score_num}</div>
                <div class="score-label">简历评分 / 100</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with col2:
        # 提取评分理由（评分标题后的第一句话）
        reason_match = re.search(r"简历评分[:：]\s*\d{1,3}/100\s*\n+(.+?)(?:\n|$)", analysis_text)
        reason = reason_match.group(1).strip() if reason_match else ""

        st.markdown(
            f'''
            <div style="padding: 8px 0;">
                <div style="font-size: 1rem; font-weight: 700; color: #0F172A; margin-bottom: 0.5rem;">
                    综合评级：{get_score_badge(score_num)}
                </div>
                <div style="font-size: 0.95rem; color: #475569; line-height: 1.6;">
                    {reason}
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with col3:
        if score_num >= 85:
            advice = "竞争力很强，可直接投递"
        elif score_num >= 70:
            advice = "稍作修改即可投递"
        elif score_num >= 60:
            advice = "建议按诊断重点优化"
        else:
            advice = "需要较大幅度修改"

        st.markdown(
            f'''
            <div style="background: #F1F5F9; border-radius: 12px; padding: 16px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 4px;">投递建议</div>
                <div style="font-size: 1rem; font-weight: 700; color: #0F172A;">{advice}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )


def parse_problems_and_suggestions(analysis_text: str) -> list[dict]:
    """
    从分析文本中提取主要问题和修改建议
    返回 [{problem, suggestion}, ...]
    """
    items = []

    # 尝试匹配 "### 主要问题" 和 "### 修改建议" 区块
    problems_match = re.search(r"#{1,3}\s*主要问题\s*\n(.*?)(?=#{1,3}\s*修改建议|$)", analysis_text, re.DOTALL)
    suggestions_match = re.search(r"#{1,3}\s*修改建议\s*\n(.*?)(?=#{1,3}|$)", analysis_text, re.DOTALL)

    problems = []
    suggestions = []

    if problems_match:
        problems_text = problems_match.group(1).strip()
        # 按行分割，过滤空行
        problems = [line.strip("-•* ").strip() for line in problems_text.split("\n") if line.strip()]

    if suggestions_match:
        suggestions_text = suggestions_match.group(1).strip()
        suggestions = [line.strip("-•* ").strip() for line in suggestions_text.split("\n") if line.strip()]

    # 配对
    for i in range(max(len(problems), len(suggestions))):
        items.append(
            {
                "problem": problems[i] if i < len(problems) else "",
                "suggestion": suggestions[i] if i < len(suggestions) else "",
            }
        )

    return items


def render_analysis_tab(analysis_text: str):
    """渲染诊断分析 tab"""
    # 提取问题/建议
    items = parse_problems_and_suggestions(analysis_text)

    if items:
        st.markdown('<div class="card-title">🔍 主要问题与修改建议</div>', unsafe_allow_html=True)
        for i, item in enumerate(items, 1):
            if not item["problem"] and not item["suggestion"]:
                continue
            with st.expander(f"问题 {i}：{item['problem'][:40]}{'...' if len(item['problem']) > 40 else ''}", expanded=False):
                if item["problem"]:
                    st.markdown(f"**❌ 问题：** {item['problem']}")
                if item["suggestion"]:
                    st.markdown(f"**✅ 建议：** {item['suggestion']}")
    else:
        st.info("未识别到结构化的问题和建议，下面是完整分析内容：")
        st.markdown(analysis_text)


def render_resume_tab(resume_text: str):
    """渲染优化后简历 tab"""
    st.markdown(
        '''
        <div class="resume-preview">
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(resume_text)
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    render_header()

    uploaded_file = render_upload_card()
    analyze_button = render_analyze_button(uploaded_file)

    if analyze_button:
        # 校验
        api_key = get_api_key()
        if not api_key:
            st.error(
                "⚠️ 未配置 DeepSeek API Key。"
                "线上请在 Streamlit Cloud Secrets 中配置；"
                "本地请在 .env 文件中配置。"
            )
            return

        if uploaded_file is None:
            st.error("⚠️ 请先上传简历 PDF")
            return

        # 步骤 1：读取 PDF
        render_progress(1)
        with st.spinner("正在读取 PDF..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                resume_text = extract_text_from_pdf(tmp_path)
                Path(tmp_path).unlink(missing_ok=True)

                if len(resume_text.strip()) < 50:
                    st.error("⚠️ 简历内容太短，可能 PDF 无法提取文字，请上传文字版 PDF")
                    return

            except Exception as e:
                st.error(f"❌ 简历读取失败：{e}")
                return

        # 步骤 2：AI 分析
        render_progress(2)
        with st.spinner("AI 正在审阅简历..."):
            try:
                result = analyze_resume(
                    resume_text=resume_text,
                    api_key=api_key,
                    model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
                    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                )
            except Exception as e:
                st.error(f"❌ AI 分析失败：{e}")
                return

        # 步骤 3：完成
        render_progress(3)

        # 拆分分析结果
        analysis_part, resume_part = split_analysis_result(result)
        score, rest = extract_score_section(analysis_part)

        # 结果区域
        st.markdown('<div class="card" style="margin-top: 2rem;">', unsafe_allow_html=True)

        if score:
            render_score_section(score, analysis_part)
        else:
            st.info("未识别到评分，下面是完整分析结果：")

        st.markdown('</div>', unsafe_allow_html=True)

        # Tabs
        tab_analysis, tab_resume = st.tabs(["💡 诊断分析", "✨ 优化后简历"])

        with tab_analysis:
            st.markdown('<div class="card" style="margin-top: 0;">', unsafe_allow_html=True)
            render_analysis_tab(analysis_part)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_resume:
            st.markdown('<div class="card" style="margin-top: 0;">', unsafe_allow_html=True)
            if resume_part:
                render_resume_tab(resume_part)
            else:
                st.warning("未从分析结果中提取到优化后的简历")
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
