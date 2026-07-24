"""
meng - AI 简历优化器
Streamlit 前端主程序
"""

import os
import re
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.resume_analyzer import analyze_resume
from src.resume_exporter import export_optimized_resume_to_docx
from src.resume_parser import extract_text_from_pdf

# 加载 .env 文件
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="meng - AI 简历优化器",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 自定义样式：深色渐变背景 + 毛玻璃卡片 + 粒子特效
st.markdown(
    """
    <style>
    /* 全局背景 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
    }

    /* 隐藏 Streamlit 顶部和底部多余元素 */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}

    /* 主内容区域 */
    .main .block-container {
        max-width: 800px;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    /* 毛玻璃卡片效果 */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        margin-bottom: 2rem;
    }

    /* 标题样式 */
    .app-title {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #FF6B6B, #fbbf24, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem !important;
    }

    .app-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* 按钮样式 */
    .stButton>button {
        width: 100%;
        border-radius: 16px;
        height: 3.2rem;
        font-size: 1.1rem;
        font-weight: 600;
        background: linear-gradient(90deg, #FF6B6B, #f472b6) !important;
        border: none !important;
        box-shadow: 0 10px 25px -5px rgba(244, 114, 182, 0.4);
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 30px -5px rgba(244, 114, 182, 0.6);
    }

    /* 文件上传区域 */
    .stFileUploader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1rem;
        border: 2px dashed rgba(255, 255, 255, 0.2);
    }

    /* 侧边栏 */
    .css-1cypcdb {background: rgba(15, 23, 42, 0.95);}

    /* 结果区域 */
    .result-box {
        background: rgba(255, 255, 255, 0.05);
        padding: 1.5rem;
        border-radius: 16px;
        border-left: 4px solid #FF6B6B;
        margin: 1rem 0;
    }

    /* 评分数字 */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #fbbf24 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 粒子背景
particles_html = """
<div class="particles-container" style="
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    overflow: hidden;
    pointer-events: none;
">
"""

for i in range(40):
    left = (i * 2.5) % 100
    delay = (i * 0.5) % 10
    duration = 10 + (i % 10)
    size = 2 + (i % 4)
    particles_html += f"""
    <div style="
        position: absolute;
        width: {size}px;
        height: {size}px;
        background: rgba(255, 255, 255, {0.3 + (i % 5) * 0.1});
        border-radius: 50%;
        left: {left}%;
        bottom: -10px;
        animation: floatUp {duration}s linear {delay}s infinite;
    "></div>
    """

particles_html += """
</div>
<style>
@keyframes floatUp {
    0% {
        transform: translateY(0) translateX(0) scale(0);
        opacity: 0;
    }
    10% {
        opacity: 1;
        transform: scale(1);
    }
    90% {
        opacity: 0.6;
    }
    100% {
        transform: translateY(-110vh) translateX(50px) scale(0.5);
        opacity: 0;
    }
}
</style>
"""

st.components.v1.html(particles_html, height=0)


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


def render_main():
    st.markdown(
        '''
        <div class="app-title">📄 meng - AI 简历优化器</div>
        <div class="app-subtitle">
            上传你的简历 PDF，AI 会在 30 秒内给出：
            简历评分 · 主要问题 · 修改建议 · 优化后的简历
        </div>
        ''',
        unsafe_allow_html=True,
    )

    # 玻璃卡片开始
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    # 文件上传
    uploaded_file = st.file_uploader(
        "上传简历 PDF",
        type=["pdf"],
        help="请上传文字版 PDF，图片扫描件可能无法识别",
    )

    if uploaded_file is not None:
        st.info(f"✅ 已上传文件：**{uploaded_file.name}**")

    # 分析按钮
    analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)

    # 玻璃卡片结束
    st.markdown('</div>', unsafe_allow_html=True)

    return uploaded_file, analyze_button


def main():
    uploaded_file, analyze_button = render_main()

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

        # 显示进度
        with st.spinner("正在读取简历内容..."):
            try:
                # 保存临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                # 解析 PDF
                resume_text = extract_text_from_pdf(tmp_path)

                # 清理临时文件
                Path(tmp_path).unlink(missing_ok=True)

                # 显示简历字数
                st.success(f"✅ 成功读取简历，共 {len(resume_text)} 字符")

            except Exception as e:
                st.error(f"❌ 简历读取失败：{e}")
                return

        with st.spinner("AI 正在分析简历，请稍候..."):
            try:
                result = analyze_resume(
                    resume_text=resume_text,
                    api_key=api_key,
                    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                )
            except Exception as e:
                st.error(f"❌ AI 分析失败：{e}")
                return

        # 结果卡片开始
        st.markdown('<div class="glass-card" style="margin-top: 2rem;">', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 分析结果")

        score, rest = extract_score_section(result)
        if score:
            # 尝试提取数字
            try:
                score_num = int(score.split("/")[0])
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("简历评分", score)
                with col2:
                    if score_num >= 80:
                        st.metric("评级", "优秀")
                    elif score_num >= 60:
                        st.metric("评级", "良好")
                    else:
                        st.metric("评级", "需改进")
                with col3:
                    st.metric("优化项", "详见下方")
            except ValueError:
                st.markdown(f"**简历评分：{score}**")

            st.markdown(rest)
        else:
            st.markdown(result)

        # 下载区域
        st.markdown("---")
        st.subheader("📥 下载结果")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📋 完整分析报告",
                data=result,
                file_name="简历优化建议.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col2:
            try:
                docx_buffer, _ = export_optimized_resume_to_docx(result)
                st.download_button(
                    label="📝 优化后简历（Word）",
                    data=docx_buffer,
                    file_name="优化后的简历.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Word 生成失败：{e}")

        # 结果卡片结束
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
