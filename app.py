"""
meng - AI 简历优化器
Streamlit 前端主程序
"""

import base64
import json
import os
import re
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
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

# 自定义样式：深色玻璃拟态
st.markdown(
    f"""
    <style>
    /* 页面背景：深色 + 星空图 */
    .stApp {{
        background:
            radial-gradient(ellipse at top, rgba(15, 23, 42, 0.75), rgba(2, 6, 23, 0.92)),
            {bg_image if bg_image else "linear-gradient(180deg, #020617 0%, #0F172A 100%)"}
            center/cover no-repeat fixed;
        color: #F8FAFC;
    }}

    /* 隐藏 Streamlit 底部和多余元素 */
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none !important;}}
    #MainMenu {{visibility: hidden;}}

    /* 主容器 */
    .main .block-container {{
        max-width: 1100px;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }}

    /* 玻璃卡片 */
    .glass-card {{
        background: rgba(15, 23, 42, 0.60);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        padding: 28px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        margin-bottom: 28px;
    }}

    .card-title {{
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
        margin-bottom: 0.75rem !important;
        letter-spacing: -0.3px;
    }}

    .card-subtitle {{
        font-size: 0.95rem;
        color: #94A3B8;
        line-height: 1.6;
    }}

    /* Hero 区域 */
    .hero {{
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
    }}

    .hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 999px;
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.25);
        color: #60A5FA;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1.25rem;
    }}

    .hero-title {{
        font-size: 3rem !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
        letter-spacing: -2px;
        margin-bottom: 0.75rem !important;
        background: linear-gradient(135deg, #F8FAFC 0%, #60A5FA 50%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .hero-subtitle {{
        font-size: 1.1rem;
        color: #94A3B8;
        line-height: 1.6;
        max-width: 560px;
        margin: 0 auto;
    }}

    /* 上传区 */
    .stFileUploader {{
        background: rgba(15, 23, 42, 0.40) !important;
        backdrop-filter: blur(12px);
        border: 2px dashed rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px;
        padding: 2rem;
    }}

    .stFileUploader:hover {{
        border-color: rgba(59, 130, 246, 0.60) !important;
        background: rgba(15, 23, 42, 0.50) !important;
    }}

    .stFileUploader label,
    .stFileUploader > div > div,
    .stFileUploader small {{
        color: #CBD5E1 !important;
    }}

    /* 按钮 */
    .stButton > button {{
        width: 100%;
        border-radius: 12px;
        height: 3rem;
        font-size: 1rem;
        font-weight: 600;
        background: linear-gradient(135deg, #3B82F6 0%, #6366F1 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.30);
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.45);
    }}

    .stButton > button:active {{
        transform: translateY(0);
    }}

    .stButton > button:disabled {{
        background: rgba(148, 163, 184, 0.30) !important;
        box-shadow: none;
    }}

    /* 评分区 */
    .score-metric {{
        text-align: center;
    }}

    .score-number {{
        font-size: 4rem;
        font-weight: 800;
        line-height: 1;
        background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }}

    .score-label {{
        font-size: 0.9rem;
        color: #94A3B8;
        font-weight: 500;
    }}

    .verdict-box {{
        background: rgba(15, 23, 42, 0.40);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        height: 100%;
    }}

    .verdict-title {{
        font-size: 0.85rem;
        color: #94A3B8;
        margin-bottom: 0.5rem;
    }}

    .verdict-text {{
        font-size: 1.05rem;
        color: #F8FAFC;
        font-weight: 600;
        line-height: 1.5;
    }}

    /* 标签 */
    .badge {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
    }}

    .badge-success {{ background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.25); }}
    .badge-info {{ background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.25); }}
    .badge-warning {{ background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.25); }}
    .badge-danger {{ background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.25); }}

    /* Tabs - pill 样式 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        border-bottom: none;
        margin-bottom: 1.5rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        padding: 10px 22px;
        font-weight: 600;
        color: #94A3B8;
        border-radius: 999px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(15, 23, 42, 0.40);
    }}

    .stTabs [aria-selected="true"] {{
        color: #FFFFFF !important;
        background: linear-gradient(135deg, #3B82F6 0%, #6366F1 100%) !important;
        border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.35);
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        font-weight: 600 !important;
        color: #F8FAFC !important;
        background: rgba(15, 23, 42, 0.40);
        border-radius: 12px;
        padding: 14px 18px !important;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .streamlit-expander {{
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        margin-bottom: 12px;
        background: rgba(15, 23, 42, 0.30);
    }}

    /* 提示框 */
    .stAlert {{
        background: rgba(15, 23, 42, 0.60) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
    }}

    .stAlert [data-testid="stMarkdownContainer"] p {{
        color: #F8FAFC !important;
    }}

    /* 分隔线 */
    hr {{
        border: none !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin: 1.5rem 0 !important;
    }}

    /* 简历预览 */
    .resume-preview {{
        background: rgba(15, 23, 42, 0.50);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px;
        line-height: 1.75;
        color: #E2E8F0;
        font-size: 0.95rem;
    }}

    .resume-preview h1,
    .resume-preview h2,
    .resume-preview h3 {{
        color: #F8FAFC !important;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }}

    .resume-preview p {{
        margin-bottom: 0.5rem;
    }}

    /* 小字说明 */
    .hint-text {{
        font-size: 0.85rem;
        color: #64748B;
        margin-top: 0.5rem;
    }}

    /* 进度条 */
    .stProgress > div > div {{
        background: linear-gradient(90deg, #3B82F6 0%, #6366F1 100%) !important;
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


def render_hero():
    """渲染顶部 Hero"""
    st.markdown(
        '''
        <div class="hero">
            <div class="hero-badge">
                ✨ AI 驱动的简历优化
            </div>
            <div class="hero-title">meng 简历优化器</div>
            <div class="hero-subtitle">
                10 年资深 HR + 行业专家视角，帮你找出简历真正的问题，直接输出能投递的优化版本
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_upload_section():
    """渲染上传区"""
    st.markdown('<div class="glass-card" style="text-align: center; max-width: 640px; margin: 0 auto 2rem auto;">', unsafe_allow_html=True)

    st.markdown(
        '''
        <div class="card-title" style="margin-bottom: 0.5rem;">📄 上传你的简历</div>
        <div class="card-subtitle" style="margin-bottom: 1.5rem;">
            支持 PDF 格式。AI 会从 HR 和业务负责人双视角分析，指出问题并输出优化后的完整简历。
        </div>
        ''',
        unsafe_allow_html=True,
    )

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
            <div class="score-metric">
                <div class="score-number">{score_num}</div>
                <div class="score-label">简历评分 / 100</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with col2:
        # 提取评分理由
        reason_match = re.search(r"简历评分[:：]\s*\d{1,3}/100\s*\n+(.+?)(?:\n|$)", analysis_text)
        reason = reason_match.group(1).strip() if reason_match else ""

        st.markdown(
            f'''
            <div class="verdict-box">
                <div class="verdict-title">综合评级</div>
                <div class="verdict-text" style="margin-bottom: 0.75rem;">{get_score_badge(score_num)}</div>
                <div class="verdict-title">评分理由</div>
                <div class="verdict-text" style="font-weight: 500; color: #CBD5E1;">{reason}</div>
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
            <div class="verdict-box">
                <div class="verdict-title">投递建议</div>
                <div class="verdict-text">{advice}</div>
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

    problems_match = re.search(r"#{1,3}\s*主要问题\s*\n(.*?)(?=#{1,3}\s*修改建议|$)", analysis_text, re.DOTALL)
    suggestions_match = re.search(r"#{1,3}\s*修改建议\s*\n(.*?)(?=#{1,3}|$)", analysis_text, re.DOTALL)

    problems = []
    suggestions = []

    if problems_match:
        problems_text = problems_match.group(1).strip()
        problems = [line.strip("-•* ").strip() for line in problems_text.split("\n") if line.strip()]

    if suggestions_match:
        suggestions_text = suggestions_match.group(1).strip()
        suggestions = [line.strip("-•* ").strip() for line in suggestions_text.split("\n") if line.strip()]

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
    items = parse_problems_and_suggestions(analysis_text)

    if items:
        st.markdown('<div class="card-title">🔍 主要问题与修改建议</div>', unsafe_allow_html=True)
        for i, item in enumerate(items, 1):
            if not item["problem"] and not item["suggestion"]:
                continue
            with st.expander(f"问题 {i}：{item['problem'][:45]}{'...' if len(item['problem']) > 45 else ''}", expanded=False):
                if item["problem"]:
                    st.markdown(f"**❌ 问题：** {item['problem']}")
                if item["suggestion"]:
                    st.markdown(f"**✅ 建议：** {item['suggestion']}")
    else:
        st.info("未识别到结构化的问题和建议，下面是完整分析内容：")
        st.markdown(analysis_text)


def render_copy_button(text: str, key: str):
    """渲染原生 JS 一键复制按钮"""
    escaped_text = json.dumps(text)
    html = f"""
    <div style="text-align: right; margin-bottom: 12px;">
        <button id="copy-btn-{key}"
                style="
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 8px 16px;
                    border-radius: 10px;
                    border: 1px solid rgba(255,255,255,0.15);
                    background: rgba(15, 23, 42, 0.60);
                    color: #CBD5E1;
                    font-size: 0.85rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-family: inherit;
                "
                onmouseover="this.style.background='rgba(59, 130, 246, 0.20)';this.style.color='#FFFFFF';this.style.borderColor='rgba(59, 130, 246, 0.40)'"
                onmouseout="this.style.background='rgba(15, 23, 42, 0.60)';this.style.color='#CBD5E1';this.style.borderColor='rgba(255,255,255,0.15)'"
        >
            📋 复制优化后简历
        </button>
    </div>
    <script>
        document.getElementById('copy-btn-{key}').addEventListener('click', function() {{
            var text = {escaped_text};
            var btn = this;
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(text).then(function() {{
                    btn.innerHTML = '✓ 已复制';
                    btn.style.color = '#34D399';
                    btn.style.borderColor = 'rgba(16, 185, 129, 0.40)';
                    setTimeout(function() {{
                        btn.innerHTML = '📋 复制优化后简历';
                        btn.style.color = '#CBD5E1';
                        btn.style.borderColor = 'rgba(255,255,255,0.15)';
                    }}, 2000);
                }}).catch(function(err) {{
                    console.error('Copy failed:', err);
                    fallbackCopy(text, btn);
                }});
            }} else {{
                fallbackCopy(text, btn);
            }}
            function fallbackCopy(textToCopy, button) {{
                var textarea = document.createElement('textarea');
                textarea.value = textToCopy;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                try {{
                    var successful = document.execCommand('copy');
                    if (successful) {{
                        button.innerHTML = '✓ 已复制';
                        button.style.color = '#34D399';
                        setTimeout(function() {{
                            button.innerHTML = '📋 复制优化后简历';
                            button.style.color = '#CBD5E1';
                        }}, 2000);
                    }} else {{
                        button.innerHTML = '❌ 复制失败';
                    }}
                }} catch (err) {{
                    button.innerHTML = '❌ 复制失败';
                }}
                document.body.removeChild(textarea);
            }}
        }});
    </script>
    """
    components.html(html, height=50)


def render_resume_tab(resume_text: str):
    """渲染优化后简历 tab"""
    render_copy_button(resume_text, key="resume-copy")

    st.markdown(
        '''
        <div class="resume-preview">
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(resume_text)
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    render_hero()

    uploaded_file = render_upload_section()
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
        st.markdown('<div class="glass-card" style="margin-top: 2rem;">', unsafe_allow_html=True)

        if score:
            render_score_section(score, analysis_part)
        else:
            st.info("未识别到评分，下面是完整分析结果：")

        st.markdown('</div>', unsafe_allow_html=True)

        # Tabs
        tab_analysis, tab_resume = st.tabs(["💡 诊断分析", "✨ 优化后简历"])

        with tab_analysis:
            st.markdown('<div class="glass-card" style="margin-top: 0;">', unsafe_allow_html=True)
            render_analysis_tab(analysis_part)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_resume:
            st.markdown('<div class="glass-card" style="margin-top: 0;">', unsafe_allow_html=True)
            if resume_part:
                render_resume_tab(resume_part)
            else:
                st.warning("未从分析结果中提取到优化后的简历")
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
