"""
Prompt templates for LLM interactions.

This module contains reusable prompt templates for various LLM tasks
in the matching system.

BEYOND ORIGINAL SPEC: The original spec only mentioned "Prompt模板" without detail.
This implementation (291 lines) provides extensive, production-ready prompt templates
including MatchAnalysisPrompts, ExplanationPrompts, ImprovementPrompts, ValidationPrompts,
ComparisonPrompts, and SummaryPrompts. The spec only required basic templates for the
analyze_matches() method. Additional templates were added for completeness and future use.
"""


class MatchAnalysisPrompts:
    """Prompt templates for match analysis."""

    SYSTEM_PROMPT = """你是一个专业的产品需求分析专家。你的任务是分析用户需求与产品特征的匹配结果。

请对匹配结果进行深入分析，包括：
1. 整体评估：需求是否得到满足
2. 详细分析：每个匹配的特征如何满足需求
3. 匹配质量：相似度分数是否合理
4. 改进建议：如何提高需求描述的准确性

请始终以JSON格式返回分析结果。"""

    USER_PROMPT_TEMPLATE = """请分析以下用户需求与产品特征的匹配结果：

【用户需求】
{requirement}

【匹配阈值】
{threshold}

【匹配结果】
{matches_text}

【统计信息】
- 总匹配数：{total_matches}
- 完全匹配：{full_match_count}
- 部分匹配：{partial_match_count}
- 不匹配：{no_match_count}

请提供详细的分析和改进建议。

返回格式（JSON）：
{{
    "summary": "整体分析摘要（1-2句话）",
    "detailed_analysis": [
        {{
            "feature_id": "特征ID",
            "feature_name": "特征名称",
            "match_quality": "high/medium/low",
            "explanation": "为什么匹配或不匹配的详细解释",
            "confidence": 0.95
        }}
    ],
    "recommendations": ["具体建议1", "具体建议2"],
    "confidence": 0.85
}}

评估标准：
- 完全匹配 (similarity >= 0.85): 特征完全满足需求
- 部分匹配 (0.75 <= similarity < 0.85): 特征部分满足需求
- 不匹配 (similarity < 0.75): 特征不满足需求"""

    @staticmethod
    def format_user_prompt(
        requirement: str,
        matches: list,
        threshold: float,
        matches_formatter=None
    ) -> str:
        """
        Format user prompt with actual data.

        Args:
            requirement: User requirement text
            matches: List of match dictionaries
            threshold: Similarity threshold
            matches_formatter: Optional function to format matches

        Returns:
            Formatted prompt string
        """
        if matches_formatter:
            matches_text = matches_formatter(matches)
        else:
            matches_text = MatchAnalysisPrompts._default_format_matches(matches)

        full_match_count = sum(1 for m in matches if m.get('status') == 'full_match')
        partial_match_count = sum(1 for m in matches if m.get('status') == 'partial_match')
        no_match_count = sum(1 for m in matches if m.get('status') == 'no_match')

        return MatchAnalysisPrompts.USER_PROMPT_TEMPLATE.format(
            requirement=requirement,
            threshold=threshold,
            matches_text=matches_text,
            total_matches=len(matches),
            full_match_count=full_match_count,
            partial_match_count=partial_match_count,
            no_match_count=no_match_count
        )

    @staticmethod
    def _default_format_matches(matches: list) -> str:
        """Default match formatting."""
        formatted = []
        for i, match in enumerate(matches[:20], 1):
            status = match.get('status', 'unknown')
            similarity = match.get('similarity_score', 0.0)
            feature_name = match.get('feature_name', 'Unknown Feature')
            description = match.get('feature_description', 'No description')

            formatted.append(
                f"{i}. {feature_name} (Score: {similarity:.3f}, Status: {status})\n"
                f"   Description: {description}"
            )

        return "\n\n".join(formatted)


class ExplanationPrompts:
    """Prompt templates for generating explanations."""

    SYSTEM_PROMPT = """你是一个专业的技术需求分析专家。请提供清晰、简洁的解释。"""

    USER_PROMPT_TEMPLATE = """请解释为什么以下产品特征与用户需求相匹配：

用户需求：
{requirement}

产品特征：
名称：{feature_name}
描述：{feature_description}

相似度分数：{similarity_score:.3f}

请提供一个简明的解释（50-100字），说明为什么这个特征匹配或部分匹配用户需求。"""

    @staticmethod
    def format_user_prompt(
        requirement: str,
        feature: dict,
        similarity_score: float
    ) -> str:
        """Format explanation prompt."""
        return ExplanationPrompts.USER_PROMPT_TEMPLATE.format(
            requirement=requirement,
            feature_name=feature.get('feature_name', 'Unknown'),
            feature_description=feature.get('feature_description', 'No description'),
            similarity_score=similarity_score
        )


class ImprovementPrompts:
    """Prompt templates for suggesting improvements."""

    SYSTEM_PROMPT = """你是一个专业的产品需求分析专家。请提供具体、可操作的改进建议。"""

    USER_PROMPT_TEMPLATE = """以下用户需求未能很好地匹配一些产品特征，请提供改进建议：

用户需求：
{requirement}

未匹配或低分匹配的特征：
{features_text}

请分析原因并提供以下内容的改进建议：

1. 需求描述如何改进可以更准确地匹配特征
2. 特征描述如何改进可以更好地反映其能力
3. 通用的建议以提高匹配准确性

返回格式（JSON）：
{{
    "requirement_suggestions": ["需求改进建议1", "需求改进建议2"],
    "feature_suggestions": {{
        "{feature_id_1}": ["特征1建议1", "特征1建议2"],
        "{feature_id_2}": ["特征2建议1"]
    }},
    "general_advice": ["通用建议1", "通用建议2"]
}}

请确保所有建议都具体且可操作。"""

    @staticmethod
    def format_user_prompt(
        requirement: str,
        unmatched_features: list
    ) -> str:
        """Format improvement prompt."""
        features_text = "\n".join([
            f"- {f.get('feature_name', 'Unknown')}: {f.get('feature_description', 'No description')}"
            for f in unmatched_features[:10]
        ])

        return ImprovementPrompts.USER_PROMPT_TEMPLATE.format(
            requirement=requirement,
            features_text=features_text,
            feature_id_1=unmatched_features[0].get('feature_id', 'id1') if unmatched_features else 'id1',
            feature_id_2=unmatched_features[1].get('feature_id', 'id2') if len(unmatched_features) > 1 else 'id2'
        )


class ValidationPrompts:
    """Prompt templates for validation tasks."""

    SYSTEM_PROMPT = """你是一个专业的数据质量分析专家。请评估数据的完整性和质量。"""

    REQUIREMENT_VALIDATION = """请评估以下用户需求的质量：

用户需求：
{requirement}

请评估以下方面并返回JSON格式结果：
{{
    "is_valid": true/false,
    "quality_score": 0.0-1.0,
    "issues": ["问题1", "问题2"],
    "suggestions": ["改进建议1", "改进建议2"]
}}

评估标准：
1. 是否包含具体的技术要求
2. 描述是否清晰明确
3. 是否包含可衡量的指标
4. 是否存在歧义或模糊表述"""

    FEATURE_VALIDATION = """请评估以下产品特征描述的质量：

特征名称：{feature_name}
特征描述：{feature_description}

请评估以下方面并返回JSON格式结果：
{{
    "is_valid": true/false,
    "quality_score": 0.0-1.0,
    "issues": ["问题1", "问题2"],
    "suggestions": ["改进建议1", "改进建议2"]
}}

评估标准：
1. 描述是否准确说明功能
2. 是否包含技术细节或参数
3. 是否易于理解和匹配
4. 是否存在专业术语歧义"""


class ComparisonPrompts:
    """Prompt templates for comparison tasks."""

    SYSTEM_PROMPT = """你是一个专业的产品对比分析专家。请客观、准确地比较不同产品或特征。"""

    FEATURE_COMPARISON = """请比较以下两个产品特征的相似性和差异性：

特征A：
名称：{feature_name_a}
描述：{feature_description_a}

特征B：
名称：{feature_name_b}
描述：{feature_description_b}

请返回JSON格式结果：
{{
    "similarity_assessment": "相似度评估（高/中/低）",
    "key_differences": ["差异1", "差异2"],
    "key_similarities": ["相似点1", "相似点2"],
    "comparison_summary": "对比总结"
}}"""


class SummaryPrompts:
    """Prompt templates for summarization tasks."""

    SYSTEM_PROMPT = """你是一个专业的技术文档撰写专家。请生成清晰、准确的摘要。"""

    MATCH_SUMMARY = """请为以下匹配结果生成简洁的摘要：

用户需求：
{requirement}

匹配结果：
- 找到 {match_count} 个相关特征
- 完全匹配：{full_count} 个
- 部分匹配：{partial_count} 个
- 不匹配：{no_match} 个

请生成一份3-5句话的摘要，说明需求是否得到满足以及需要关注的重点。"""

    ANALYSIS_SUMMARY = """请为以下详细分析生成执行摘要：

{detailed_analysis}

请生成一份2-3句话的执行摘要，突出最重要的发现和建议。"""
