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

# 自定义样式：我的世界（Minecraft）风格 - 精致封面级
st.markdown(
    """
    <style>
    /* 导入像素字体 */
    @import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Press+Start+2P&display=swap');

    /* 全局背景：多层天空渐变 */
    .stApp {
        background:
            linear-gradient(180deg,
                #4FC3F7 0%,
                #64B5F6 20%,
                #90CAF9 40%,
                #B3E5FC 55%,
                transparent 55%),
            linear-gradient(180deg,
                #7CB342 55%,
                #689F38 65%,
                #558B2F 80%,
                #33691E 100%);
        background-attachment: fixed;
        background-size: 100% 100%;
        position: relative;
    }

    /* 场景层：远山 */
    .stApp::before {
        content: "";
        position: fixed;
        left: 0;
        right: 0;
        top: 30%;
        height: 25%;
        background-image:
            linear-gradient(180deg, transparent 0%, transparent 40%, #78909C 40%, #78909C 60%, #90A4AE 60%, #90A4AE 80%, #B0BEC5 80%, #B0BEC5 100%);
        clip-path: polygon(
            0% 100%, 0% 70%,
            5% 55%, 10% 65%, 15% 40%, 20% 55%, 25% 35%, 30% 50%,
            38% 25%, 45% 45%, 52% 30%, 60% 50%, 68% 20%, 75% 45%,
            82% 30%, 90% 50%, 95% 40%, 100% 55%, 100% 100%
        );
        z-index: -2;
        opacity: 0.8;
        pointer-events: none;
    }

    /* 场景层：草地纹理 + 树 */
    .stApp::after {
        content: "";
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        height: 40%;
        background:
            /* 树1 */
            radial-gradient(circle at 12% 65%, #2E7D32 0%, #2E7D32 4%, transparent 4.5%),
            radial-gradient(circle at 12% 62%, #388E3C 0%, #388E3C 5%, transparent 5.5%),
            /* 树2 */
            radial-gradient(circle at 88% 70%, #2E7D32 0%, #2E7D32 5%, transparent 5.5%),
            radial-gradient(circle at 88% 66%, #388E3C 0%, #388E3C 6%, transparent 6.5%),
            /* 树3 */
            radial-gradient(circle at 35% 80%, #2E7D32 0%, #2E7D32 3%, transparent 3.5%),
            /* 树4 */
            radial-gradient(circle at 72% 78%, #2E7D32 0%, #2E7D32 3.5%, transparent 4%);
        z-index: -1;
        pointer-events: none;
    }

    /* 隐藏 Streamlit 顶部和底部多余元素 */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}
    #MainMenu {visibility: hidden;}

    /* 主内容区域 */
    .main .block-container {
        max-width: 820px;
        padding-top: 2rem;
        padding-bottom: 2rem;
        position: relative;
        z-index: 10;
    }

    /* Minecraft 风格卡片：橡木箱质感 */
    .glass-card {
        background:
            linear-gradient(180deg,
                #6D4C2E 0%,
                #5D3E24 3%,
                #6D4C2E 6%,
                #5D3E24 100%);
        border: none;
        border-radius: 0px;
        padding: 2rem;
        box-shadow:
            0 0 0 3px #3E2A18,
            0 0 0 6px #8B6F47,
            0 0 0 9px #3E2A18,
            0 10px 0 6px rgba(0, 0, 0, 0.4),
            0 15px 30px rgba(0, 0, 0, 0.6);
        margin-bottom: 2.5rem;
        color: #f0f0d8;
        position: relative;
        image-rendering: pixelated;
    }

    /* 卡片内木纹装饰 */
    .glass-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            repeating-linear-gradient(180deg,
                transparent 0px,
                transparent 20px,
                rgba(62, 42, 24, 0.15) 20px,
                rgba(62, 42, 24, 0.15) 21px),
            repeating-linear-gradient(90deg,
                transparent 0px,
                transparent 40px,
                rgba(62, 42, 24, 0.1) 40px,
                rgba(62, 42, 24, 0.1) 41px);
        pointer-events: none;
    }

    /* 标题：Minecraft LOGO 风格 */
    .app-title {
        font-family: 'ZCOOL KuaiLe', 'Press Start 2P', cursive !important;
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        color: #f0f0d8 !important;
        text-align: center;
        margin: 1rem 0 0.5rem 0 !important;
        letter-spacing: 3px;
        text-shadow:
            4px 4px 0 #3E2A18,
            -1px -1px 0 #3E2A18,
            2px -1px 0 #3E2A18,
            -1px 2px 0 #3E2A18,
            2px 2px 0 #3E2A18,
            0 0 20px rgba(0, 0, 0, 0.5);
        image-rendering: pixelated;
    }

    .app-subtitle {
        text-align: center;
        color: #FFF9C4;
        font-size: 1.15rem;
        font-family: 'ZCOOL KuaiLe', sans-serif !important;
        margin-bottom: 2.5rem;
        text-shadow:
            2px 2px 0 #3E2A18,
            0 0 10px rgba(0, 0, 0, 0.6);
        letter-spacing: 1px;
    }

    /* Minecraft 风格按钮：草方块 */
    .stButton>button {
        width: 100%;
        border-radius: 0px;
        height: 3.5rem;
        font-size: 1.3rem;
        font-weight: 700;
        font-family: 'ZCOOL KuaiLe', sans-serif !important;
        letter-spacing: 2px;
        background:
            linear-gradient(180deg,
                #8BC34A 0%,
                #7CB342 30%,
                #689F38 70%,
                #558B2F 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        text-shadow:
            2px 2px 0 #33691E,
            -1px -1px 0 #33691E,
            1px -1px 0 #33691E,
            -1px 1px 0 #33691E;
        box-shadow:
            0 0 0 3px #33691E,
            0 0 0 6px #8BC34A,
            0 0 0 9px #33691E,
            0 6px 0 6px #2E5920,
            0 8px 15px rgba(0, 0, 0, 0.4);
        transition: all 0.1s ease;
        image-rendering: pixelated;
    }

    .stButton>button:hover {
        background:
            linear-gradient(180deg,
                #9CCC65 0%,
                #8BC34A 30%,
                #7CB342 70%,
                #689F38 100%) !important;
        transform: translateY(-2px);
    }

    .stButton>button:active {
        transform: translateY(4px);
        box-shadow:
            0 0 0 3px #33691E,
            0 0 0 6px #8BC34A,
            0 0 0 9px #33691E,
            0 2px 0 6px #2E5920;
    }

    /* 下载按钮：金色钻石风 */
    .stDownloadButton>button {
        background:
            linear-gradient(180deg,
                #FFD54F 0%,
                #FFC107 40%,
                #FFA000 80%,
                #FF8F00 100%) !important;
        box-shadow:
            0 0 0 3px #E65100,
            0 0 0 6px #FFB300,
            0 0 0 9px #E65100,
            0 6px 0 6px #BF360C,
            0 8px 15px rgba(0, 0, 0, 0.4) !important;
        text-shadow: 2px 2px 0 #BF360C !important;
    }

    /* 文件上传区：木箱 */
    .stFileUploader {
        background:
            linear-gradient(180deg,
                rgba(139, 111, 71, 0.3) 0%,
                rgba(93, 62, 36, 0.4) 100%);
        border: 3px dashed #8B6F47 !important;
        border-radius: 0px;
        padding: 1.5rem;
    }

    .stFileUploader label,
    .stFileUploader > div > div,
    .stFileUploader small {
        color: #FFF9C4 !important;
        font-family: 'ZCOOL KuaiLe', sans-serif !important;
    }

    /* 结果区域 */
    .result-box {
        background: rgba(60, 50, 35, 0.85);
        padding: 1.5rem;
        border-radius: 0px;
        border: 3px solid #8B6F47;
        border-left: 6px solid #7CB342;
        margin: 1rem 0;
    }

    /* 评分数字：金色 */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #FFD700 !important;
        text-shadow:
            2px 2px 0 #3E2A18,
            0 0 15px rgba(255, 215, 0, 0.4) !important;
        font-family: 'ZCOOL KuaiLe', sans-serif !important;
    }

    [data-testid="stMetricLabel"] {
        color: #FFF9C4 !important;
        font-family: 'ZCOOL KuaiLe', sans-serif !important;
    }

    /* 小标题 */
    h1, h2, h3, .streamlit-expanderHeader {
        color: #FFF9C4 !important;
        font-family: 'ZCOOL KuaiLe', sans-serif !important;
        text-shadow: 2px 2px 0 #3E2A18;
        letter-spacing: 1px;
    }

    /* 普通文字 */
    .glass-card p,
    .glass-card li,
    .glass-card span,
    .glass-card div {
        color: #f0f0d8 !important;
        font-family: 'ZCOOL KuaiLe', sans-serif !important;
    }

    /* 强调加粗文字：金色 */
    .glass-card strong,
    .glass-card b {
        color: #FFD700 !important;
    }

    /* 链接 */
    a {
        color: #FFD700 !important;
        text-decoration: none !important;
    }

    a:hover {
        color: #FFC107 !important;
        text-decoration: underline !important;
    }

    /* 提示框 */
    .stAlert {
        background: rgba(45, 35, 25, 0.9) !important;
        border: 3px solid #8B6F47 !important;
        border-radius: 0px !important;
    }

    .stAlert p {
        color: #FFF9C4 !important;
    }

    /* 分隔线 */
    hr {
        border: none !important;
        border-top: 3px dashed #8B6F47 !important;
        margin: 1.5rem 0 !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #7CB342 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Minecraft 场景：飘浮的方块云 + 掉落的方块
particles_html = """
<div class="mc-scene" style="
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

# 云朵（像素风）
cloud_positions = [
    (10, 8, 12), (45, 5, 18), (75, 12, 10), (25, 18, 8), (85, 22, 14)
]
for left, top, duration in cloud_positions:
    particles_html += f"""
    <div style="
        position: absolute;
        left: {left}%;
        top: {top}%;
        width: 80px;
        height: 30px;
        background: white;
        box-shadow:
            -20px 0 0 0 white,
            20px 0 0 0 white,
            40px -10px 0 0 white,
            -40px -10px 0 0 white,
            0 -15px 0 0 white,
            25px -20px 0 0 white,
            -25px -20px 0 0 white;
        opacity: 0.9;
        animation: cloudDrift {duration}s linear infinite;
        image-rendering: pixelated;
    "></div>
    """

# Minecraft 方块颜色（更真实）
block_colors = [
    ("#7CB342", "#558B2F"),   # 草方块顶
    ("#8D6E63", "#5D4037"),   # 泥土
    ("#9E9E9E", "#616161"),   # 石头
    ("#FFD54F", "#F57C00"),   # 金子
    ("#8D6E63", "#5D4037"),   # 木头
    ("#4FC3F7", "#0288D1"),   # 钻石
    ("#FF7043", "#D84315"),   # 红石
    ("#EEEEEE", "#BDBDBD"),   # 铁块
]

# 掉落的方块（更多，更真实）
for i in range(45):
    left = (i * 2.3) % 100
    delay = (i * 0.35) % 10
    duration = 8 + (i % 10)
    size = 12 + (i % 4) * 4
    rotate = (i * 30) % 360
    color, border = block_colors[i % len(block_colors)]
    particles_html += f"""
    <div style="
        position: absolute;
        width: {size}px;
        height: {size}px;
        background: {color};
        box-shadow:
            inset -{size//4}px -{size//4}px 0 rgba(0,0,0,0.3),
            inset {size//4}px {size//4}px 0 rgba(255,255,255,0.25);
        left: {left}%;
        top: -30px;
        animation: blockFall {duration}s linear {delay}s infinite;
        image-rendering: pixelated;
        transform: rotate({rotate}deg);
    "></div>
    """

particles_html += """
</div>
<style>
@keyframes blockFall {
    0% {
        transform: translateY(-30px) rotate(0deg);
        opacity: 0;
    }
    5% {
        opacity: 0.7;
    }
    95% {
        opacity: 0.6;
    }
    100% {
        transform: translateY(110vh) rotate(360deg);
        opacity: 0;
    }
}

@keyframes cloudDrift {
    0% { transform: translateX(-50px); }
    100% { transform: translateX(calc(100vw + 100px)); }
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
    # Minecraft LOGO 风格标题
    st.markdown(
        '''
        <div style="text-align: center; margin: 1rem 0 0 0;">
            <div class="app-title">⛏️ MENG ⛏️</div>
            <div style="
                font-family: 'ZCOOL KuaiLe', sans-serif;
                font-size: 1.4rem;
                color: #FFD700;
                text-shadow: 3px 3px 0 #3E2A18, 0 0 15px rgba(0,0,0,0.6);
                letter-spacing: 4px;
                margin-top: -0.5rem;
                margin-bottom: 0.5rem;
            ">
                AI 简历优化器
            </div>
            <div class="app-subtitle">
                📦 上传简历 · 30 秒挖出一份更值钱的简历 📦<br/>
                <span style="font-size: 0.9rem; color: #FFF9C4;">
                    💎 简历评分 · ⚔️ 主要问题 · 📜 修改建议 · ✨ 优化后简历
                </span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    # 玻璃卡片开始
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    # 文件上传
    uploaded_file = st.file_uploader(
        "📦 打开背包 - 上传简历 PDF",
        type=["pdf"],
        help="请上传文字版 PDF，扫描件/图片可能无法识别",
    )

    if uploaded_file is not None:
        st.info(f"✅ 已装填：**{uploaded_file.name}**")

    # 分析按钮
    analyze_button = st.button("⛏️  开 始 挖 掘 简 历  ⛏️", type="primary", use_container_width=True)

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
                    model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
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
