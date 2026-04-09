import re
from pathlib import Path
from typing import Optional
import json

from agentscope.tool import ToolResponse

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


class KnowledgeSegment:
    def __init__(self, title: str, content: str, topic: str, source_file: str):
        self.title = title.strip()
        self.content = content.strip()
        self.topic = topic
        self.source_file = source_file

    def __repr__(self):
        return f"KnowledgeSegment(title={self.title!r}, topic={self.topic!r})"

    def to_text(self) -> str:
        return f"## {self.title}\n{self.content}"

    def match_score(self, query_keywords: list[str]) -> int:
        """计算与查询关键词的匹配得分"""
        score = 0
        text = f"{self.title} {self.content}".lower()
        for kw in query_keywords:
            if kw.lower() in text:
                score += 1
        return score


def split_segments_by_headers(content: str) -> list[tuple[str, str]]:
    """按 ## 二级标题拆分内容为片段
    
    Returns:
        list of (title, content) tuples
    """
    segments = []
    
    parts = content.split("\n## ")
    for i, part in enumerate(parts):
        if i == 0:
            continue
        
        lines = part.split("\n", 1)
        if len(lines) >= 2:
            title = lines[0].strip()
            body = lines[1].strip()
            segments.append((title, body))
        elif lines:
            title = lines[0].strip()
            segments.append((title, ""))
    
    return segments


def build_segment_index(knowledge_dir: Path) -> dict[str, list[dict]]:
    """构建片段索引 {topic: [{title, content, source_file}]}"""
    index = {}

    if not knowledge_dir.exists():
        return index

    for md_file in knowledge_dir.rglob("*.md"):
        if md_file.name == "00-index.md":
            continue

        topic = md_file.stem.split("-", 1)[-1] if "-" in md_file.stem else md_file.stem
        content = md_file.read_text(encoding="utf-8")

        segments = split_segments_by_headers(content)

        index[topic] = []
        for title, seg_content in segments:
            index[topic].append({
                "title": title,
                "content": seg_content,
                "source_file": str(md_file.relative_to(knowledge_dir.parent))
            })

    return index


_segment_index: dict[str, list[dict]] | None = None


def get_segment_index() -> dict[str, list[dict]]:
    global _segment_index
    if _segment_index is None:
        _segment_index = build_segment_index(KNOWLEDGE_DIR)
    return _segment_index


def extract_keywords(query: str) -> list[str]:
    """从查询中提取关键词（去除停用词）"""
    stopwords = {
        "的", "是", "在", "有", "和", "与", "或", "一个", "这个", "那个",
        "如何", "怎么", "什么", "哪些", "为什么", "是否",
        "the", "a", "an", "is", "are", "in", "on", "to", "of", "and", "or",
        "how", "what", "why", "which", "can", "should", "would"
    }

    words = re.findall(r"[\w\u4e00-\u9fff]+", query.lower())
    keywords = [w for w in words if len(w) > 1 and w not in stopwords]

    return keywords


def search_segments(
    query: str,
    topic: str | None = None,
    max_segments: int = 3
) -> list[KnowledgeSegment]:
    """根据查询搜索最相关的知识片段"""
    index = get_segment_index()
    keywords = extract_keywords(query)

    if not keywords:
        return []

    scored_segments = []

    topics_to_search = [topic] if topic else index.keys()

    for t in topics_to_search:
        if t not in index:
            continue

        for seg_info in index[t]:
            seg = KnowledgeSegment(
                title=seg_info["title"],
                content=seg_info["content"],
                topic=t,
                source_file=seg_info["source_file"]
            )
            score = seg.match_score(keywords)
            if score > 0:
                scored_segments.append((score, seg))

    scored_segments.sort(key=lambda x: -x[0])
    return [seg for _, seg in scored_segments[:max_segments]]


def query_knowledge(
    query: str,
    topic: str | None = None,
    max_segments: int = 3
) -> ToolResponse:
    """查询知识库，获取与SQL性能问题相关的知识片段。

    Args:
        query: 查询问题，如"全表扫描如何识别"
        topic: 可选，限定主题(full_table_scan, missing_index, slow_query等)
        max_segments: 最多返回的片段数，默认3

    Returns:
        匹配的知识片段文本
    """
    try:
        if not KNOWLEDGE_DIR.exists():
            return ToolResponse(content="知识库目录不存在")

        segments = search_segments(query, topic, max_segments)

        if not segments:
            topics = list(get_segment_index().keys())
            return ToolResponse(
                content=f"未找到匹配的知识片段。可用主题: {', '.join(topics)}"
            )

        lines = []
        for seg in segments:
            lines.append(f"## {seg.title}")
            lines.append(f"*来源: {seg.source_file}*")
            lines.append("")
            lines.append(seg.content[:500] if len(seg.content) > 500 else seg.content)
            lines.append("\n---\n")

        result = f"找到 {len(segments)} 个相关片段:\n\n" + "\n".join(lines)
        return ToolResponse(content=result)

    except Exception as e:
        return ToolResponse(content=f"查询知识库出错: {str(e)}")


def list_topics() -> ToolResponse:
    """列出知识库中所有可用主题"""
    try:
        index = get_segment_index()
        if not index:
            return ToolResponse(content="知识库为空")

        lines = ["可用的知识主题:"]
        for topic, segments in index.items():
            lines.append(f"- {topic} ({len(segments)} 个片段)")

        return ToolResponse(content="\n".join(lines))
    except Exception as e:
        return ToolResponse(content=f"获取主题列表出错: {str(e)}")


if __name__ == "__main__":
    print("=== 测试知识检索 ===\n")

    print("1. 查询 '全表扫描':")
    result = query_knowledge("全表扫描如何识别")
    print(result.content[:300])
    print("...\n")

    print("2. 查询 '索引缺失':")
    result = query_knowledge("索引缺失")
    print(result.content[:300])
    print("...\n")

    print("3. 列出所有主题:")
    result = list_topics()
    print(result.content)
