"""
Test suite for Phase 2 prompt templates.

Tests cover:
- PromptTemplate base class functionality
- EnhancedMatchAnalysisPrompts (full and quick versions)
- KeywordExtractionPrompts
- MismatchDetectionPrompts
- Versioning and A/B testing support
- JSON output format validation

Total: 10 test cases
"""

import unittest
from apps.llm.prompts import (
    PromptTemplate,
    EnhancedMatchAnalysisPrompts,
    KeywordExtractionPrompts,
    MismatchDetectionPrompts
)


class TestPromptTemplate(unittest.TestCase):
    """Test suite for PromptTemplate base class."""

    def test_01_template_creation(self):
        """Test 1: Verify PromptTemplate can be created with all parameters."""
        template = PromptTemplate(
            name="test_template",
            version="1.0",
            variant_name="A",
            system_prompt="You are a test assistant.",
            user_prompt_template="Test: {variable}",
            output_schema={"type": "object"},
            metadata={"author": "test"}
        )

        assert template.name == "test_template"
        assert template.version == "1.0"
        assert template.variant_name == "A"
        assert template.system_prompt == "You are a test assistant."
        assert template.user_prompt_template == "Test: {variable}"
        assert template.metadata == {"author": "test"}

    def test_02_full_name_property(self):
        """Test 2: Verify full_name property generates correct name format."""
        template = PromptTemplate(
            name="enhanced_analysis",
            version="2.0",
            variant_name="B"
        )

        assert template.full_name == "enhanced_analysis_v2.0_B"

    def test_03_format_method(self):
        """Test 3: Verify format method correctly interpolates variables."""
        template = PromptTemplate(
            name="test",
            version="1.0",
            user_prompt_template="Analyze: {requirement} with threshold {threshold}"
        )

        formatted = template.format(requirement="User needs X", threshold=0.75)
        assert formatted == "Analyze: User needs X with threshold 0.75"

    def test_04_format_missing_variable(self):
        """Test 4: Verify format raises KeyError for missing variables."""
        template = PromptTemplate(
            name="test",
            version="1.0",
            user_prompt_template="Analyze: {requirement} and {feature}"
        )

        with self.assertRaises(KeyError) as exc_info:
            template.format(requirement="User needs X")

        self.assertIn("Missing required variable", str(exc_info.exception))

    def test_05_get_formatted_prompts(self):
        """Test 5: Verify get_formatted_prompts returns system and user prompts."""
        template = PromptTemplate(
            name="test",
            version="1.0",
            system_prompt="System prompt here",
            user_prompt_template="User: {input}"
        )

        system, user = template.get_formatted_prompts(input="test input")
        assert system == "System prompt here"
        assert user == "User: test input"

    def test_06_validate_output(self):
        """Test 6: Verify validate_output checks required fields."""
        schema = {
            "type": "object",
            "required": ["field1", "field2"]
        }
        template = PromptTemplate(
            name="test",
            version="1.0",
            output_schema=schema
        )

        # Valid output
        valid_output = {"field1": "value1", "field2": "value2"}
        assert template.validate_output(valid_output) is True

        # Invalid output (missing required field)
        invalid_output = {"field1": "value1"}
        assert template.validate_output(invalid_output) is False

    def test_07_to_dict_serialization(self):
        """Test 7: Verify to_dict correctly serializes template."""
        template = PromptTemplate(
            name="test",
            version="1.0",
            variant_name="control",
            system_prompt="System",
            user_prompt_template="User: {var}",
            output_schema={"type": "object"},
            metadata={"description": "Test template"}
        )

        template_dict = template.to_dict()

        assert template_dict["name"] == "test"
        assert template_dict["version"] == "1.0"
        assert template_dict["variant_name"] == "control"
        assert template_dict["full_name"] == "test_v1.0_control"
        assert template_dict["system_prompt"] == "System"
        assert template_dict["user_prompt_template"] == "User: {var}"
        assert template_dict["output_schema"] == {"type": "object"}
        assert template_dict["metadata"] == {"description": "Test template"}

    def test_08_enhanced_match_analysis_full_mode(self):
        """Test 8: Verify EnhancedMatchAnalysisPrompts full mode formatting."""
        candidates = [
            {
                "feature_id": "f1",
                "feature_name": "Data Export",
                "feature_description": "Export data to CSV format",
                "similarity_score": 0.89
            },
            {
                "feature_id": "f2",
                "feature_name": "Data Import",
                "feature_description": "Import data from Excel",
                "similarity_score": 0.76
            }
        ]

        formatted = EnhancedMatchAnalysisPrompts.format_user_prompt(
            requirement="Need to export reports",
            candidates=candidates,
            mode="full"
        )

        # Verify key elements are present
        assert "Need to export reports" in formatted
        assert "Data Export" in formatted
        assert "Data Import" in formatted
        assert "Export data to CSV format" in formatted
        assert "0.890" in formatted or "0.89" in formatted
        assert "feature_id" in formatted
        assert "is_valid_match" in formatted

    def test_09_enhanced_match_analysis_quick_mode(self):
        """Test 9: Verify EnhancedMatchAnalysisPrompts quick mode formatting."""
        candidates = [
            {
                "feature_id": "f1",
                "feature_name": "Data Export",
                "feature_description": "Export to CSV",
                "similarity_score": 0.89
            }
        ]

        formatted = EnhancedMatchAnalysisPrompts.format_user_prompt(
            requirement="Need export",
            candidates=candidates,
            mode="quick"
        )

        # Quick mode should be simpler
        assert "Need export" in formatted
        assert "Data Export" in formatted
        # Quick mode should NOT include description
        assert "Export to CSV" not in formatted
        # Should still have core fields
        assert "feature_id" in formatted
        assert "is_valid_match" in formatted

    def test_10_prompt_template_instances(self):
        """Test 10: Verify get_prompt_template returns correct PromptTemplate instances."""
        # Test full version
        full_template = EnhancedMatchAnalysisPrompts.get_prompt_template(mode="full")
        assert full_template.name == "enhanced_match_analysis"
        assert full_template.version == "1.0"
        assert full_template.variant_name == "full"
        assert "analysis_summary" in full_template.output_schema["required"]
        assert full_template.metadata.get("target_tokens") == 2000

        # Test quick version
        quick_template = EnhancedMatchAnalysisPrompts.get_prompt_template(mode="quick")
        assert quick_template.name == "enhanced_match_analysis"
        assert quick_template.variant_name == "quick"
        assert "total_valid_matches" in quick_template.output_schema["required"]
        assert quick_template.metadata.get("target_tokens") == 500

        # Test keyword extraction template
        keyword_template = KeywordExtractionPrompts.get_prompt_template()
        assert keyword_template.name == "keyword_extraction"
        assert "requirement_keywords" in keyword_template.output_schema["required"]

        # Test mismatch detection template
        mismatch_template = MismatchDetectionPrompts.get_prompt_template()
        assert mismatch_template.name == "mismatch_detection"
        assert "is_valid_match" in mismatch_template.output_schema["required"]
        assert mismatch_template.metadata.get("target_tokens") == 800


class TestKeywordExtractionPrompts(unittest.TestCase):
    """Additional tests for KeywordExtractionPrompts."""

    def test_format_user_prompt(self):
        """Verify keyword extraction prompt formatting."""
        formatted = KeywordExtractionPrompts.format_user_prompt(
            requirement="Need data export functionality",
            feature_description="Export data to CSV and Excel formats"
        )

        assert "Need data export functionality" in formatted
        assert "Export data to CSV and Excel formats" in formatted
        assert "requirement_keywords" in formatted
        assert "feature_keywords" in formatted
        assert "shared_keywords" in formatted


class TestMismatchDetectionPrompts(unittest.TestCase):
    """Additional tests for MismatchDetectionPrompts."""

    def test_format_user_prompt(self):
        """Verify mismatch detection prompt formatting."""
        formatted = MismatchDetectionPrompts.format_user_prompt(
            requirement="Need PDF export",
            feature_name="Data Export",
            feature_description="Export to CSV",
            similarity_score=0.87,
            original_status="full_match"
        )

        assert "Need PDF export" in formatted
        assert "Data Export" in formatted
        assert "0.870" in formatted or "0.87" in formatted
        assert "full_match" in formatted
        assert "is_valid_match" in formatted
        assert "corrected_status" in formatted


class TestVersioningAndABTesting(unittest.TestCase):
    """Tests for versioning and A/B testing support."""

    def test_version_comparison(self):
        """Test that different versions can coexist."""
        v1 = PromptTemplate(name="test", version="1.0", variant_name="A")
        v2 = PromptTemplate(name="test", version="2.0", variant_name="A")

        assert v1.full_name == "test_v1.0_A"
        assert v2.full_name == "test_v2.0_A"
        assert v1.full_name != v2.full_name

    def test_ab_testing_variants(self):
        """Test that A/B testing variants work correctly."""
        control = PromptTemplate(name="test", version="1.0", variant_name="control")
        treatment = PromptTemplate(name="test", version="1.0", variant_name="treatment")

        assert control.full_name == "test_v1.0_control"
        assert treatment.full_name == "test_v1.0_treatment"
        assert control.full_name != treatment.full_name

    def test_metadata_tracking(self):
        """Test that metadata can track experiments and results."""
        template = PromptTemplate(
            name="ab_test",
            version="1.0",
            variant_name="B",
            metadata={
                "experiment": "enhanced_prompts",
                "start_date": "2025-01-30",
                "success_rate": 0.92
            }
        )

        assert template.metadata["experiment"] == "enhanced_prompts"
        assert template.metadata["success_rate"] == 0.92


class TestBackwardCompatibility(unittest.TestCase):
    """Tests to ensure backward compatibility with existing prompt classes."""

    def test_existing_classes_still_work(self):
        """Verify that existing prompt classes (MatchAnalysisPrompts, etc.) still work."""
        from apps.llm.prompts import MatchAnalysisPrompts, ExplanationPrompts

        # Test MatchAnalysisPrompts
        matches = [
            {
                "feature_name": "Test Feature",
                "feature_description": "Test description",
                "similarity_score": 0.85,
                "status": "full_match"
            }
        ]

        formatted = MatchAnalysisPrompts.format_user_prompt(
            requirement="Test requirement",
            matches=matches,
            threshold=0.75
        )

        assert "Test requirement" in formatted
        assert "Test Feature" in formatted

        # Test ExplanationPrompts
        feature = {
            "feature_name": "Test",
            "feature_description": "Test desc"
        }

        formatted = ExplanationPrompts.format_user_prompt(
            requirement="Need test",
            feature=feature,
            similarity_score=0.90
        )

        assert "Need test" in formatted
        assert "Test" in formatted
