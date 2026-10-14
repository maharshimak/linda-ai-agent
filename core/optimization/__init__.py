"""
Core Optimization Module for MAK AI
Provides A/B testing and content optimization tools.
"""

from .ab_testing import (
    VideoVariantGenerator,
    VariantConfig,
    VariantType,
    GeneratedVariant,
    ABTestResult,
    generate_ab_test,
    get_variant_templates
)

__all__ = [
    "VideoVariantGenerator",
    "VariantConfig",
    "VariantType",
    "GeneratedVariant",
    "ABTestResult",
    "generate_ab_test",
    "get_variant_templates"
]
