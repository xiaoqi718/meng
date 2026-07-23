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
from src.resume_parser import extract_text_from_pdf

# 加载 .env 文件
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="meng - AI 简历优化器",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 自定义样式
st.markdown(
    """
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-size: 1.1rem;
    }
    .result-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_score_section(text: str) -> tuple[str, str]:
    """
    从 AI 输出中提取评分部分
    返回 (评分部分, 剩余内容)
    """
    score_match = re.search(r"## 简历评分[:：]\s*(\d{1,3}/100)", text)
    if score_match:
        score = score_match.group(1)
        rest = text[score_match.end():].strip()
        return score, rest
    return "", text


# 侧边栏
def render_sidebar():
    st.sidebar.title("⚙️ 设置")

    # API Key
    env_key = os.getenv("DEEPSEEK_API_KEY", "")
    api_key = st.sidebar.text_input(
        "DeepSeek API Key",
        value=env_key,
        type="password",
        placeholder="请输入你的 API Key",
        help="没有 API Key？去 platform.deepseek.com 注册获取",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 关于 meng")
    st.sidebar.markdown("上传简历 PDF，AI 帮你优化，让简历更值钱。")

    return api_key


# 主界面
def render_main():
    st.title("📄 meng - AI 简历优化器")
    st.markdown(
        """
        <p style="font-size: 1.1rem; color: #666;">
        上传你的简历 PDF，AI 会在 30 秒内给出：
        简历评分 · 主要问题 · 修改建议 · 优化后的简历
        </p>
        """,
        unsafe_allow_html=True,
    )

    # 文件上传
    uploaded_file = st.file_uploader(
        "上传简历 PDF",
        type=["pdf"],
        help="请上传文字版 PDF，图片扫描件可能无法识别",
    )

    if uploaded_file is not None:
        st.info(f"已上传文件：**{uploaded_file.name}**")

    # 分析按钮
    analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)

    return uploaded_file, analyze_button


def main():
    api_key = render_sidebar()
    uploaded_file, analyze_button = render_main()

    if analyze_button:
        # 校验
        if not api_key:
            st.error("⚠️ 请先输入 DeepSeek API Key")
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

        # 展示结果
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

        # 复制按钮
        st.markdown("---")
        st.download_button(
            label="📋 下载完整分析结果",
            data=result,
            file_name="简历优化建议.md",
            mime="text/markdown",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
