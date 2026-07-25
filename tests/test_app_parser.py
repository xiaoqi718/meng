"""
app.py 解析函数的单元测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import (
    ChangeBlock,
    extract_score_section,
    parse_change_blocks,
    split_analysis_result,
)


def test_parse_change_blocks_basic():
    text = """
===CHANGE_BLOCK_START===
===SECTION===
工作经历-字节跳动-产品经理
===ORIGINAL===
负责日常产品工作。
===MODIFIED===
负责抖音电商导购链路优化。
===REASON===
原句问题：太笼统。
HR/业务负责人反应：无法判断能力。
改后预期：更有针对性。
===CHANGE_BLOCK_END===
"""
    blocks = parse_change_blocks(text)
    assert len(blocks) == 1
    assert blocks[0].section == "工作经历-字节跳动-产品经理"
    assert blocks[0].original == "负责日常产品工作。"
    assert blocks[0].modified == "负责抖音电商导购链路优化。"
    assert "太笼统" in blocks[0].reason


def test_parse_change_blocks_multiple():
    text = """
===CHANGE_BLOCK_START===
===SECTION===
A
===ORIGINAL===
a
===MODIFIED===
a1
===REASON===
r1
===CHANGE_BLOCK_END===

===CHANGE_BLOCK_START===
===SECTION===
B
===ORIGINAL===
b
===MODIFIED===
b1
===REASON===
r2
===CHANGE_BLOCK_END===
"""
    blocks = parse_change_blocks(text)
    assert len(blocks) == 2
    assert blocks[1].section == "B"


def test_parse_change_blocks_empty():
    assert parse_change_blocks("没有块") == []
    assert parse_change_blocks("") == []


def test_extract_score_section():
    text = "### 简历评分：72/100\n\n理由：整体能过初筛。"
    score, rest = extract_score_section(text)
    assert score == "72/100"
    assert "整体能过初筛" in rest


def test_split_analysis_result():
    text = "some analysis\n===OPTIMIZED_RESUME_START===\noptimized\n===OPTIMIZED_RESUME_END==="
    analysis, resume = split_analysis_result(text)
    assert analysis == "some analysis"
    assert resume == "optimized"


def test_change_block_dataclass():
    block = ChangeBlock(section="s", original="o", modified="m", reason="r")
    assert block.original == "o"
