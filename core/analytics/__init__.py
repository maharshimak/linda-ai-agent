"""
Core Analytics Module for MAK AI
Provides viral potential analysis and content optimization.
"""

from .hook_scorer import (
    ViralHookAnalyzer,
    HookScore,
    SceneData,
    HookPattern,
    analyze_hook,
    get_hook_score,
    is_viral_hook
)

__all__ = [
    "ViralHookAnalyzer",
    "HookScore",
    "SceneData",
    "HookPattern",
    "analyze_hook",
    "get_hook_score",
    "is_viral_hook"
]
