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


# =============================================================================
# PHASE 2: Enhanced Prompt Templates with Versioning and A/B Testing
# =============================================================================

class PromptTemplate:
    """
    Base class for versioned and A/B testable prompt templates.

    Features:
    - Semantic versioning (v1.0, v2.0)
    - A/B testing support (variant_name: "A" | "B" or "control" | "treatment")
    - Variable interpolation using Python .format()
    - JSON output format enforcement

    Usage:
        prompt = PromptTemplate(
            name="enhanced_match_analysis",
            version="2.0",
            variant_name="A",
            system_prompt="You are an expert...",
            user_prompt_template="Analyze: {requirement}",
            output_schema={
                "type": "object",
                "properties": {...}
            }
        )
        formatted = prompt.format(requirement="User needs X")
    """

    def __init__(
        self,
        name: str,
        version: str,
        variant_name: str = "A",
        system_prompt: str = "",
        user_prompt_template: str = "",
        output_schema: dict = None,
        metadata: dict = None
    ):
        """
        Initialize a prompt template.

        Args:
            name: Template name (e.g., "enhanced_match_analysis")
            version: Semantic version (e.g., "1.0", "2.0")
            variant_name: A/B test variant ("A", "B", "control", "treatment")
            system_prompt: System prompt text
            user_prompt_template: User prompt template with {variable} placeholders
            output_schema: JSON schema for expected output format
            metadata: Additional metadata (description, author, tags, etc.)
        """
        self.name = name
        self.version = version
        self.variant_name = variant_name
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.output_schema = output_schema or {}
        self.metadata = metadata or {}

    @property
    def full_name(self) -> str:
        """Get full template name with version and variant."""
        return f"{self.name}_v{self.version}_{self.variant_name}"

    def format(self, **kwargs) -> str:
        """
        Format user prompt template with provided variables.

        Args:
            **kwargs: Variables to interpolate into the template

        Returns:
            Formatted user prompt string

        Raises:
            KeyError: If required variable is missing
        """
        try:
            return self.user_prompt_template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Missing required variable for template '{self.full_name}': {e}")

    def get_formatted_prompts(self, **kwargs) -> tuple:
        """
        Get both system and formatted user prompts.

        Args:
            **kwargs: Variables to interpolate into user prompt

        Returns:
            Tuple of (system_prompt, formatted_user_prompt)
        """
        return self.system_prompt, self.format(**kwargs)

    def get_output_format_instruction(self) -> str:
        """
        Generate instruction text for output format based on schema.

        Returns:
            String describing expected output format
        """
        if not self.output_schema:
            return ""

        return f"\n\n请严格按照以下JSON格式返回结果：\n{self.output_schema}"

    def validate_output(self, output: dict) -> bool:
        """
        Validate LLM output against the expected schema.

        Args:
            output: LLM output dictionary

        Returns:
            True if output matches schema, False otherwise
        """
        # Basic validation: check required fields
        required_fields = self.output_schema.get("required", [])
        for field in required_fields:
            if field not in output:
                return False
        return True

    def to_dict(self) -> dict:
        """Serialize template to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "variant_name": self.variant_name,
            "full_name": self.full_name,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "output_schema": self.output_schema,
            "metadata": self.metadata
        }


class EnhancedMatchAnalysisPrompts:
    """
    Enhanced match analysis prompts with full and quick versions.

    Features:
    - Full version: ~2000 tokens output, detailed analysis
    - Quick version: ~500 tokens output, 3-4 core fields
    - Shared system prompt for consistency
    - Structured JSON output
    """

    # Shared system prompt
    SYSTEM_PROMPT = """你是一个专业的产品能力匹配分析专家。你的任务是深入分析用户需求与产品特征的匹配关系。

你需要评估：
1. 匹配的正确性：特征是否真正满足需求
2. 匹配的完整性：是否有遗漏的重要方面
3. 置信度评估：向量相似度是否反映真实匹配程度
4. 误配检测：识别可能存在的错误匹配

请始终返回严格的JSON格式结果，不要包含任何额外文字说明。"""

    # Full version user prompt template (target: ~2000 tokens output)
    USER_PROMPT_FULL_TEMPLATE = """请分析以下用户需求与产品特征的匹配结果：

【用户需求】
{requirement}

【候选特征列表】
{candidates_text}

请对每个候选特征进行详细分析，返回JSON格式结果：

{{
    "analysis_summary": "整体分析摘要（2-3句话）",
    "match_details": [
        {{
            "feature_id": "特征ID",
            "feature_name": "特征名称",
            "is_valid_match": true/false,
            "confidence_score": 0.95,
            "match_reason": "详细说明为什么匹配或不匹配",
            "keywords_from_requirement": ["关键词1", "关键词2"],
            "keywords_from_feature": ["关键词1", "关键词2"],
            "similarity_assessment": "相似度分数是否合理（合理/偏高/偏低）",
            "improvement_suggestion": "如何改进需求描述或特征描述"
        }}
    ],
    "overall_assessment": {{
        "total_matches": 5,
        "valid_matches": 4,
        "false_positives": 1,
        "confidence": 0.85
    }},
    "recommendations": ["改进建议1", "改进建议2"]
}}

评估标准：
- is_valid_match: 综合考虑语义和实际功能，判断是否为真实匹配
- confidence_score: 0.0-1.0，表示对判断的确信程度
- keywords_from_requirement: 需求中的关键技术词或功能词
- keywords_from_feature: 特征描述中的对应关键词
- similarity_assessment: 评估向量相似度分数是否准确反映匹配程度

请确保分析客观、准确、具体。"""

    # Quick version user prompt template (target: ~500 tokens output)
    USER_PROMPT_QUICK_TEMPLATE = """请快速分析以下用户需求与产品特征的匹配：

【用户需求】
{requirement}

【候选特征】
{candidates_text}

返回JSON格式结果（仅核心字段）：

{{
    "match_details": [
        {{
            "feature_id": "特征ID",
            "feature_name": "特征名称",
            "is_valid_match": true/false,
            "match_reason": "简要说明",
            "confidence_score": 0.90
        }}
    ],
    "total_valid_matches": 3
}}"""

    @staticmethod
    def format_user_prompt(
        requirement: str,
        candidates: list,
        mode: str = "full"
    ) -> str:
        """
        Format user prompt for enhanced match analysis.

        Args:
            requirement: User requirement text
            candidates: List of candidate feature dictionaries
            mode: "full" or "quick"

        Returns:
            Formatted user prompt string
        """
        # Format candidates list
        candidates_text = EnhancedMatchAnalysisPrompts._format_candidates(
            candidates, mode=mode
        )

        # Select template based on mode
        if mode == "quick":
            template = EnhancedMatchAnalysisPrompts.USER_PROMPT_QUICK_TEMPLATE
        else:
            template = EnhancedMatchAnalysisPrompts.USER_PROMPT_FULL_TEMPLATE

        return template.format(
            requirement=requirement,
            candidates_text=candidates_text
        )

    @staticmethod
    def _format_candidates(candidates: list, mode: str = "full") -> str:
        """Format candidate features for prompt."""
        formatted = []
        for i, candidate in enumerate(candidates[:20], 1):
            feature_name = candidate.get('feature_name', 'Unknown')
            description = candidate.get('feature_description', 'No description')
            similarity = candidate.get('similarity_score', 0.0)

            if mode == "quick":
                formatted.append(
                    f"{i}. {feature_name} (相似度: {similarity:.3f})"
                )
            else:
                formatted.append(
                    f"{i}. {feature_name}\n"
                    f"   描述: {description}\n"
                    f"   相似度: {similarity:.3f}"
                )

        return "\n\n".join(formatted)

    @staticmethod
    def get_prompt_template(mode: str = "full") -> PromptTemplate:
        """
        Get a PromptTemplate instance for enhanced match analysis.

        Args:
            mode: "full" or "quick"

        Returns:
            PromptTemplate instance
        """
        output_schema_full = {
            "type": "object",
            "required": ["analysis_summary", "match_details", "overall_assessment"],
            "properties": {
                "analysis_summary": {"type": "string"},
                "match_details": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["feature_id", "is_valid_match", "confidence_score"],
                        "properties": {
                            "feature_id": {"type": "string"},
                            "feature_name": {"type": "string"},
                            "is_valid_match": {"type": "boolean"},
                            "confidence_score": {"type": "number"},
                            "match_reason": {"type": "string"},
                            "keywords_from_requirement": {"type": "array", "items": {"type": "string"}},
                            "keywords_from_feature": {"type": "array", "items": {"type": "string"}},
                            "similarity_assessment": {"type": "string"},
                            "improvement_suggestion": {"type": "string"}
                        }
                    }
                },
                "overall_assessment": {
                    "type": "object",
                    "required": ["total_matches", "valid_matches", "confidence"],
                    "properties": {
                        "total_matches": {"type": "integer"},
                        "valid_matches": {"type": "integer"},
                        "false_positives": {"type": "integer"},
                        "confidence": {"type": "number"}
                    }
                },
                "recommendations": {"type": "array", "items": {"type": "string"}}
            }
        }

        output_schema_quick = {
            "type": "object",
            "required": ["match_details", "total_valid_matches"],
            "properties": {
                "match_details": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["feature_id", "is_valid_match", "confidence_score"],
                        "properties": {
                            "feature_id": {"type": "string"},
                            "feature_name": {"type": "string"},
                            "is_valid_match": {"type": "boolean"},
                            "match_reason": {"type": "string"},
                            "confidence_score": {"type": "number"}
                        }
                    }
                },
                "total_valid_matches": {"type": "integer"}
            }
        }

        if mode == "quick":
            return PromptTemplate(
                name="enhanced_match_analysis",
                version="1.0",
                variant_name="quick",
                system_prompt=EnhancedMatchAnalysisPrompts.SYSTEM_PROMPT,
                user_prompt_template=EnhancedMatchAnalysisPrompts.USER_PROMPT_QUICK_TEMPLATE,
                output_schema=output_schema_quick,
                metadata={"description": "Quick match analysis with core fields", "target_tokens": 500}
            )
        else:
            return PromptTemplate(
                name="enhanced_match_analysis",
                version="1.0",
                variant_name="full",
                system_prompt=EnhancedMatchAnalysisPrompts.SYSTEM_PROMPT,
                user_prompt_template=EnhancedMatchAnalysisPrompts.USER_PROMPT_FULL_TEMPLATE,
                output_schema=output_schema_full,
                metadata={"description": "Full match analysis with detailed fields", "target_tokens": 2000}
            )


class KeywordExtractionPrompts:
    """
    Keyword extraction prompts for requirement and feature analysis.

    Extracts relevant keywords from both requirement and feature descriptions
    to support matching and highlighting.
    """

    SYSTEM_PROMPT = """你是一个专业的文本关键词提取专家。你的任务是从需求描述和特征描述中提取关键技术词和功能词。

关注：
1. 技术术语和专有名词
2. 功能性动词和操作
3. 性能指标和参数
4. 领域特定词汇

请返回JSON格式结果。"""

    USER_PROMPT_TEMPLATE = """请从以下文本中提取关键词：

【需求文本】
{requirement}

【特征描述】
{feature_description}

返回JSON格式结果：

{{
    "requirement_keywords": ["关键词1", "关键词2", "关键词3"],
    "feature_keywords": ["关键词1", "关键词2", "关键词3"],
    "shared_keywords": ["共同关键词1", "共同关键词2"],
    "key_concepts": ["核心概念1", "核心概念2"]
}}

提取原则：
1. 优先提取技术和功能相关词汇
2. 包含重要的动词和名词
3. 忽略通用停用词（的、了、是等）
4. 最多提取10个关键词"""

    @staticmethod
    def format_user_prompt(requirement: str, feature_description: str) -> str:
        """Format keyword extraction prompt."""
        return KeywordExtractionPrompts.USER_PROMPT_TEMPLATE.format(
            requirement=requirement,
            feature_description=feature_description
        )

    @staticmethod
    def get_prompt_template() -> PromptTemplate:
        """Get PromptTemplate instance for keyword extraction."""
        output_schema = {
            "type": "object",
            "required": ["requirement_keywords", "feature_keywords", "shared_keywords"],
            "properties": {
                "requirement_keywords": {"type": "array", "items": {"type": "string"}},
                "feature_keywords": {"type": "array", "items": {"type": "string"}},
                "shared_keywords": {"type": "array", "items": {"type": "string"}},
                "key_concepts": {"type": "array", "items": {"type": "string"}}
            }
        }

        return PromptTemplate(
            name="keyword_extraction",
            version="1.0",
            variant_name="A",
            system_prompt=KeywordExtractionPrompts.SYSTEM_PROMPT,
            user_prompt_template=KeywordExtractionPrompts.USER_PROMPT_TEMPLATE,
            output_schema=output_schema,
            metadata={"description": "Extract keywords from requirements and features"}
        )


class MismatchDetectionPrompts:
    """
    Mismatch detection prompts for identifying false positive matches.

    Performs binary classification on whether a match is valid or not,
    with detailed reasoning.
    """

    SYSTEM_PROMPT = """你是一个专业的匹配质量评估专家。你的任务是判断产品特征与用户需求的匹配是否正确。

你需要考虑：
1. 语义相似性：描述内容是否真正相关
2. 功能匹配：特征是否能实际满足需求
3. 上下文理解：在业务场景中是否合理
4. 边界情况：识别可能存在的误配

请返回严格的JSON格式结果。"""

    USER_PROMPT_TEMPLATE = """请判断以下匹配是否正确：

【用户需求】
{requirement}

【产品特征】
特征名称：{feature_name}
特征描述：{feature_description}

【向量相似度】
{similarity_score:.3f}

【原始匹配状态】
{original_status}

请进行独立判断，不要被向量相似度或原始状态影响。返回JSON格式结果：

{{
    "is_valid_match": true/false,
    "confidence_score": 0.0-1.0,
    "reason": "详细说明判断依据，包括为什么匹配或不匹配",
    "similarity_reliable": true/false,
    "corrected_status": "full_match/partial_match/no_match"
}}

判断标准：
- is_valid_match: 综合判断该匹配是否正确
- confidence_score: 对判断的确信程度（0.0-1.0）
- reason: 详细说明判断理由，引用需求和特征中的具体内容
- similarity_reliable: 向量相似度是否准确反映了匹配程度
- corrected_status: 如果原始状态错误，提供正确的分类

如果以下情况，应判断为不匹配：
- 需求要求的功能与特征功能不同
- 领域或场景不相关
- 相似度来源仅仅是表面文字相似而非实际功能"""

    @staticmethod
    def format_user_prompt(
        requirement: str,
        feature_name: str,
        feature_description: str,
        similarity_score: float,
        original_status: str
    ) -> str:
        """Format mismatch detection prompt."""
        return MismatchDetectionPrompts.USER_PROMPT_TEMPLATE.format(
            requirement=requirement,
            feature_name=feature_name,
            feature_description=feature_description,
            similarity_score=similarity_score,
            original_status=original_status
        )

    @staticmethod
    def get_prompt_template() -> PromptTemplate:
        """Get PromptTemplate instance for mismatch detection."""
        output_schema = {
            "type": "object",
            "required": ["is_valid_match", "confidence_score", "reason"],
            "properties": {
                "is_valid_match": {"type": "boolean"},
                "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "reason": {"type": "string"},
                "similarity_reliable": {"type": "boolean"},
                "corrected_status": {"type": "string", "enum": ["full_match", "partial_match", "no_match"]}
            }
        }

        return PromptTemplate(
            name="mismatch_detection",
            version="1.0",
            variant_name="A",
            system_prompt=MismatchDetectionPrompts.SYSTEM_PROMPT,
            user_prompt_template=MismatchDetectionPrompts.USER_PROMPT_TEMPLATE,
            output_schema=output_schema,
            metadata={"description": "Detect false positive matches", "target_tokens": 800}
        )
