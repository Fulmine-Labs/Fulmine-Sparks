"""
Content moderation service for filtering unsafe prompts.
Uses keyword-based detection with configurable thresholds.
"""

from typing import Tuple
from ..config import settings


class ModerationService:
    """Service for content moderation and safety filtering."""
    
    # Unsafe keywords and phrases
    UNSAFE_KEYWORDS = {
        # Explicit content
        "explicit", "pornographic", "xxx", "adult", "nsfw",
        "nude", "naked", "sex", "sexual", "erotic",
        
        # Violence
        "violence", "violent", "gore", "blood", "kill", "murder",
        "weapon", "gun", "bomb", "terrorist", "terrorism",
        
        # Hate speech
        "hate", "racist", "racism", "sexist", "sexism",
        "discriminate", "discrimination", "slur",
        
        # Illegal activities
        "illegal", "crime", "criminal", "drug", "cocaine",
        "heroin", "meth", "steal", "robbery", "fraud",
        
        # Self-harm
        "suicide", "self-harm", "cutting", "overdose",
    }
    
    @staticmethod
    def score_prompt(prompt: str) -> float:
        """
        Score a prompt for unsafe content.
        
        Args:
            prompt: The text prompt to score
            
        Returns:
            Score between 0.0 (safe) and 1.0 (unsafe)
        """
        if not prompt:
            return 0.0
        
        prompt_lower = prompt.lower()
        unsafe_count = 0
        
        for keyword in ModerationService.UNSAFE_KEYWORDS:
            if keyword in prompt_lower:
                unsafe_count += 1
        
        # Calculate score based on keyword matches
        # More matches = higher score
        max_keywords = len(ModerationService.UNSAFE_KEYWORDS)
        score = min(unsafe_count / max(max_keywords / 10, 1), 1.0)
        
        return score
    
    @staticmethod
    def is_safe(prompt: str, threshold: float = None) -> Tuple[bool, float, str]:
        """
        Check if a prompt is safe to process.
        
        Args:
            prompt: The text prompt to check
            threshold: Safety threshold (0.0-1.0). Defaults to config setting.
            
        Returns:
            Tuple of (is_safe, score, reason)
        """
        if threshold is None:
            threshold = settings.MODERATION_THRESHOLD
        
        score = ModerationService.score_prompt(prompt)
        is_safe = score < threshold
        
        if not is_safe:
            reason = f"Content flagged as unsafe (score: {score:.2f})"
        else:
            reason = "Content passed moderation"
        
        return is_safe, score, reason
    
    @staticmethod
    def check_and_raise(prompt: str, threshold: float = None) -> None:
        """
        Check prompt and raise exception if unsafe.
        
        Args:
            prompt: The text prompt to check
            threshold: Safety threshold (0.0-1.0)
            
        Raises:
            ValueError: If prompt is unsafe
        """
        is_safe, score, reason = ModerationService.is_safe(prompt, threshold)
        
        if not is_safe:
            raise ValueError(f"Prompt rejected by moderation: {reason}")


# Global moderation service instance
moderation_service = ModerationService()
