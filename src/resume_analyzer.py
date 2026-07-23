"""
AI 简历分析模块
负责调用大模型分析简历并生成优化建议
"""

from openai import OpenAI


SYSTEM_PROMPT = """你是一位资深 HR 和职业发展顾问，拥有 10 年以上简历筛选和优化经验。
你的任务是从专业 HR 的角度分析用户的简历，并给出具体可执行的修改建议。

请严格按照以下格式输出：

## 简历评分：XX/100

给出 0-100 的评分，并简要说明评分依据。

## 主要问题

列出 3-5 个简历中的主要问题。每个问题用一句话说明，具体指出问题所在。

## 修改建议

针对上面的每个问题，给出具体、可执行的修改建议。建议要具体，不要泛泛而谈。

## 优化后的简历

基于原简历内容，重新写一份优化后的简历。要求：
- 保持原简历的基本信息和经历
- 使用更专业、更有冲击力的表达
- 突出成果和数据（STAR 法则）
- 语言简洁有力
- 结构清晰

注意：
- 只输出分析结果，不要输出其他无关内容
- 如果简历内容缺失重要信息（如联系方式、教育背景、工作经历），请在建议中明确指出
- 优化后的简历要真实可信，不要编造不存在的经历
"""


def analyze_resume(
    resume_text: str,
    api_key: str,
    model: str = "deepseek-chat",
    base_url: str = "https://api.deepseek.com/v1",
) -> str:
    """
    调用大模型分析简历

    Args:
        resume_text: 从 PDF 提取的简历文本
        api_key: DeepSeek API Key
        model: 模型名称
        base_url: API 基础地址

    Returns:
        AI 分析结果（Markdown 格式）
    """
    if not api_key:
        raise ValueError("API Key 不能为空")

    if not resume_text or len(resume_text.strip()) < 50:
        raise ValueError("简历内容太短，请检查 PDF 是否能正常提取文本")

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"请分析并优化以下简历：\n\n---\n\n{resume_text}\n\n---"},
            ],
            temperature=0.7,
            max_tokens=4000,
        )

        result = response.choices[0].message.content
        return result

    except Exception as e:
        raise RuntimeError(f"AI 分析失败: {e}")
