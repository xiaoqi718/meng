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

# 自定义样式：我的世界（Minecraft）风格
st.markdown(
    """
    <style>
    /* 导入像素字体 */
    @import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Press+Start+2P&display=swap');

    /* 全局背景：天空 + 草地 */
    .stApp {
        background: linear-gradient(180deg, #87CEEB 0%, #87CEEB 35%, #5D8C2E 35%, #3d5c1f 100%);
        background-attachment: fixed;
    }

    /* 隐藏 Streamlit 顶部和底部多余元素 */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}

    /* 主内容区域 */
    .main .block-container {
        max-width: 820px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* 我的世界风格卡片：像箱子/工作台面板 */
    .glass-card {
        background: rgba(45, 35, 25, 0.92);
        border: 4px solid #8B7355;
        border-radius: 0px;
        padding: 2rem;
        box-shadow:
            inset 0 0 0 4px #5C4033,
            0 8px 0 0 #2a1f15,
            0 12px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 2rem;
        color: #f0f0d8;
        position: relative;
    }

    /* 卡片内角像素装饰 */
    .glass-card::before {
        content: "";
        position: absolute;
        top: 4px;
        left: 4px;
        right: 4px;
        bottom: 4px;
        border: 2px solid #6b8c42;
        pointer-events: none;
    }

    /* 标题样式：像素风 */
    .app-title {
        font-family: 'ZCOOL KuaiLe', 'Press Start 2P', cursive !important;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        color: #f0f0d8 !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        text-shadow:
            3px 3px 0 #2a1f15,
            -1px -1px 0 #2a1f15,
            1px -1px 0 #2a1f15,
            -1px 1px 0 #2a1f15,
            1px 1px 0 #2a1f15;
    }

    .app-subtitle {
        text-align: center;
        color: #f0f0d8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 0 #2a1f15;
    }

    /* 我的世界风格按钮 */
    .stButton>button {
        width: 100%;
        border-radius: 0px;
        height: 3.2rem;
        font-size: 1.2rem;
        font-weight: 700;
        font-family: 'ZCOOL KuaiLe', sans-serif !important;
        background: linear-gradient(180deg, #7CB342 0%, #5D8C2E 100%) !important;
        border: 3px solid #4a7025 !important;
        box-shadow:
            inset 0 2px 0 rgba(255,255,255,0.3),
            0 6px 0 #3d5c1f,
            0 8px 10px rgba(0,0,0,0.3);
        color: #f0f0d8 !important;
        text-shadow: 2px 2px 0 #2a1f15;
        transition: all 0.1s ease;
    }

    .stButton>button:hover {
        background: linear-gradient(180deg, #8BC34A 0%, #6B9E2F 100%) !important;
        transform: translateY(-1px);
    }

    .stButton>button:active {
        transform: translateY(4px);
        box-shadow:
            inset 0 2px 0 rgba(255,255,255,0.3),
            0 2px 0 #3d5c1f,
            0 4px 5px rgba(0,0,0,0.3);
    }

    /* 文件上传区域：像箱子 */
    .stFileUploader {
        background: rgba(139, 115, 85, 0.3);
        border: 3px dashed #8B7355;
        border-radius: 0px;
        padding: 1.5rem;
    }

    .stFileUploader > div > div {
        color: #f0f0d8 !important;
    }

    /* 结果区域 */
    .result-box {
        background: rgba(60, 50, 35, 0.8);
        padding: 1.5rem;
        border-radius: 0px;
        border: 3px solid #8B7355;
        border-left: 6px solid #7CB342;
        margin: 1rem 0;
    }

    /* 评分数字 */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #FFD700 !important;
        text-shadow: 2px 2px 0 #2a1f15;
    }

    [data-testid="stMetricLabel"] {
        color: #f0f0d8 !important;
    }

    /* 小标题 */
    .streamlit-expanderHeader,
    h1, h2, h3 {
        color: #f0f0d8 !important;
        text-shadow: 2px 2px 0 #2a1f15;
    }

    /* 普通文字 */
    p, li, span {
        color: #f0f0d8;
    }

    /* 链接 */
    a {
        color: #FFD700 !important;
    }

    /* info / success / warning 提示框 */
    .stAlert {
        background: rgba(45, 35, 25, 0.9) !important;
        border: 2px solid #8B7355 !important;
        border-radius: 0px !important;
        color: #f0f0d8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 我的世界方块粒子背景
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

# Minecraft 风格的方块颜色
block_colors = [
    ("#5D8C2E", "#4a7025"),  # 草方块
    ("#8B7355", "#6b5a42"),  # 泥土
    ("#808080", "#606060"),  # 石头
    ("#FFD700", "#B8860B"),  # 金子
    ("#A0522D", "#8B4513"),  # 木头
    ("#87CEEB", "#5F9EA0"),  # 钻石/天空
]

for i in range(35):
    left = (i * 3.2) % 100
    delay = (i * 0.4) % 8
    duration = 6 + (i % 8)
    size = 8 + (i % 3) * 4
    color, border = block_colors[i % len(block_colors)]
    particles_html += f"""
    <div style="
        position: absolute;
        width: {size}px;
        height: {size}px;
        background: {color};
        border: 2px solid {border};
        left: {left}%;
        top: -20px;
        animation: blockFall {duration}s linear {delay}s infinite;
        image-rendering: pixelated;
    "></div>
    """

particles_html += """
</div>
<style>
@keyframes blockFall {
    0% {
        transform: translateY(0) rotate(0deg);
        opacity: 0;
    }
    10% {
        opacity: 0.8;
    }
    90% {
        opacity: 0.6;
    }
    100% {
        transform: translateY(110vh) rotate(360deg);
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


def render_main():
    st.markdown(
        '''
        <div class="app-title">⛏️ meng · AI 简历优化器</div>
        <div class="app-subtitle">
            上传你的简历 PDF，30 秒挖出一份更值钱的简历<br/>
            简历评分 · 主要问题 · 修改建议 · 优化后简历
        </div>
        ''',
        unsafe_allow_html=True,
    )

    # 玻璃卡片开始
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    # 文件上传
    uploaded_file = st.file_uploader(
        "📦 上传简历 PDF（拖入此处或点击选择文件）",
        type=["pdf"],
        help="请上传文字版 PDF，扫描件/图片可能无法识别",
    )

    if uploaded_file is not None:
        st.info(f"✅ 已上传：**{uploaded_file.name}**")

    # 分析按钮
    analyze_button = st.button("⛏️ 开始挖掘简历", type="primary", use_container_width=True)

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
        with st.spinner("⛏️ 正在挖掘简历内容..."):
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

        with st.spinner("🧪 AI 正在熔炼简历，请稍候..."):
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

        # 拆分分析结果和优化后的简历
        analysis_part, resume_part = split_analysis_result(result)

        # 分析结果卡片
        st.markdown('<div class="glass-card" style="margin-top: 2rem;">', unsafe_allow_html=True)
        st.subheader("💎 分析结果")

        score, rest = extract_score_section(analysis_part)
        if score:
            try:
                score_num = int(score.split("/")[0])
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("简历评分", score)
                with col2:
                    if score_num >= 80:
                        st.metric("评级", "钻石级")
                    elif score_num >= 60:
                        st.metric("评级", "铁级")
                    else:
                        st.metric("评级", "木级")
                with col3:
                    st.metric("优化项", "详见下方")
            except ValueError:
                st.markdown(f"**简历评分：{score}**")

            st.markdown(rest)
        else:
            st.markdown(analysis_part)

        st.markdown('</div>', unsafe_allow_html=True)

        # 优化后的简历卡片
        if resume_part:
            st.markdown('<div class="glass-card" style="margin-top: 2rem;">', unsafe_allow_html=True)
            st.subheader("✨ 优化后的简历")
            st.markdown(resume_part)

            # 下载区域
            st.markdown("---")
            st.subheader("📥 下载战利品")

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📜 完整分析报告",
                    data=result,
                    file_name="简历优化建议.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            with col2:
                try:
                    docx_buffer, _ = export_optimized_resume_to_docx(result)
                    st.download_button(
                        label="📘 优化后简历（Word）",
                        data=docx_buffer,
                        file_name="优化后的简历.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"⚠️ Word 生成失败：{e}")

            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
