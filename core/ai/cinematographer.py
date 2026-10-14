"""
AI Cinematographer
Generates camera directions, shot compositions, and movement plans.
"""
import logging
import math
from typing import Tuple, Optional, List
from dataclasses import dataclass

from ..models import CameraMove, Emotion, ScriptBeat
from ..utils.helpers import lerp, ease_out_cubic, ease_out_expo

log = logging.getLogger("core.ai.cinematographer")


@dataclass
class ShotPlan:
    """Complete shot plan for a scene."""
    camera_move: CameraMove
    start_scale: float
    end_scale: float
    offset_x: int
    offset_y: int
    rotation: float  # degrees
    shot_type: str  # "wide", "medium", "close", "extreme_close"
    focus_point: Tuple[float, float]  # normalized 0-1


# Shot type recommendations based on content
SHOT_RECOMMENDATIONS = {
    "landscape": "wide",
    "person": "medium", 
    "face": "close",
    "detail": "extreme_close",
    "action": "wide",
    "dialogue": "medium",
    "emotion": "close",
    "establishing": "wide"
}


class Cinematographer:
    """
    AI-powered virtual Director of Photography.
    Plans camera movements, compositions, and visual dynamics.
    """
    
    def __init__(self):
        self.default_scale = 1.1  # Slight oversizing for movement room
    
    def plan_shot(
        self, 
        beat: ScriptBeat,
        duration: float,
        previous_move: Optional[CameraMove] = None
    ) -> ShotPlan:
        """
        Create a shot plan for a scene beat.
        Considers the content, emotion, and previous shot to ensure variety.
        """
        camera_move = beat.camera_move
        
        # Avoid repeating the same move twice
        if previous_move and camera_move == previous_move:
            camera_move = self._alternate_move(camera_move)
        
        # Get movement parameters
        start_scale, end_scale, offset = self._get_movement_params(camera_move, duration)
        
        # Determine shot type from content
        shot_type = self._analyze_shot_type(beat)
        
        # Determine rotation (only for Dutch angle)
        rotation = 0.0
        if camera_move == CameraMove.DUTCH_ANGLE:
            rotation = 8.0  # Subtle dutch tilt
        
        # Focus point (center by default, could be enhanced with face detection)
        focus_point = (0.5, 0.5)
        
        return ShotPlan(
            camera_move=camera_move,
            start_scale=start_scale,
            end_scale=end_scale,
            offset_x=offset[0],
            offset_y=offset[1],
            rotation=rotation,
            shot_type=shot_type,
            focus_point=focus_point
        )
    
    def _get_movement_params(
        self, 
        move: CameraMove, 
        duration: float
    ) -> Tuple[float, float, Tuple[int, int]]:
        """
        Get scale and offset parameters for a camera movement.
        Returns: (start_scale, end_scale, (offset_x, offset_y))
        """
        params = {
            CameraMove.DOLLY_IN: (1.15, 1.05, (0, 0)),
            CameraMove.DOLLY_OUT: (1.05, 1.15, (0, 0)),
            CameraMove.PAN_RIGHT: (1.10, 1.10, (-80, 0)),
            CameraMove.PAN_LEFT: (1.10, 1.10, (80, 0)),
            CameraMove.CRANE_UP: (1.08, 1.08, (0, 60)),
            CameraMove.CRANE_DOWN: (1.08, 1.08, (0, -60)),
            CameraMove.ORBIT: (1.10, 1.10, (50, 30)),
            CameraMove.PARALLAX: (1.08, 1.12, (40, 0)),
            CameraMove.DUTCH_ANGLE: (1.10, 1.10, (30, 0)),
            CameraMove.STATIC: (1.02, 1.02, (0, 0)),
        }
        return params.get(move, params[CameraMove.DOLLY_IN])
    
    def _alternate_move(self, current: CameraMove) -> CameraMove:
        """Get an alternative camera movement to avoid repetition."""
        alternatives = {
            CameraMove.DOLLY_IN: CameraMove.PAN_RIGHT,
            CameraMove.DOLLY_OUT: CameraMove.PAN_LEFT,
            CameraMove.PAN_RIGHT: CameraMove.DOLLY_IN,
            CameraMove.PAN_LEFT: CameraMove.DOLLY_OUT,
            CameraMove.CRANE_UP: CameraMove.DOLLY_IN,
            CameraMove.CRANE_DOWN: CameraMove.PAN_RIGHT,
            CameraMove.ORBIT: CameraMove.PARALLAX,
            CameraMove.PARALLAX: CameraMove.DOLLY_IN,
            CameraMove.DUTCH_ANGLE: CameraMove.DOLLY_IN,
            CameraMove.STATIC: CameraMove.DOLLY_IN,
        }
        return alternatives.get(current, CameraMove.DOLLY_IN)
    
    def _analyze_shot_type(self, beat: ScriptBeat) -> str:
        """Analyze beat content to determine shot type."""
        text_lower = beat.visual_prompt.lower()
        
        # Check for keywords
        if any(word in text_lower for word in ["landscape", "city", "mountain", "ocean", "sky"]):
            return "wide"
        elif any(word in text_lower for word in ["face", "expression", "eyes", "portrait"]):
            return "close"
        elif any(word in text_lower for word in ["detail", "hand", "object", "close-up"]):
            return "extreme_close"
        elif any(word in text_lower for word in ["action", "running", "fighting", "crowd"]):
            return "wide"
        else:
            return "medium"
    
    def apply_movement(
        self,
        base_size: Tuple[int, int],
        plan: ShotPlan,
        t: float,
        duration: float
    ) -> Tuple[float, Tuple[int, int]]:
        """
        Calculate the scale and offset for a given time in the shot.
        
        Args:
            base_size: (width, height) of the canvas
            plan: The shot plan
            t: Current time in the shot
            duration: Total shot duration
            
        Returns:
            (scale, (offset_x, offset_y))
        """
        if duration <= 0:
            duration = 0.001
            
        progress = min(max(t / duration, 0), 1)
        eased = ease_out_cubic(progress)
        
        # Interpolate scale
        scale = lerp(plan.start_scale, plan.end_scale, eased)
        
        # Calculate offset based on movement type
        if plan.camera_move == CameraMove.ORBIT:
            # Circular motion
            offset_x = int(plan.offset_x * math.sin(eased * math.pi))
            offset_y = int(plan.offset_y * math.cos(eased * math.pi))
        elif plan.camera_move == CameraMove.PARALLAX:
            # Sine wave motion
            offset_x = int(plan.offset_x * math.sin(eased * 2 * math.pi))
            offset_y = 0
        elif plan.camera_move in [CameraMove.PAN_LEFT, CameraMove.PAN_RIGHT]:
            # Linear pan
            offset_x = int(plan.offset_x * eased)
            offset_y = 0
        elif plan.camera_move in [CameraMove.CRANE_UP, CameraMove.CRANE_DOWN]:
            # Linear vertical
            offset_x = 0
            offset_y = int(plan.offset_y * eased)
        else:
            # Zoom movements (DOLLY_IN, DOLLY_OUT, STATIC)
            offset_x = 0
            offset_y = 0
        
        return scale, (offset_x, offset_y)
    
    def plan_sequence(
        self,
        beats: List[ScriptBeat],
        durations: List[float]
    ) -> List[ShotPlan]:
        """
        Plan a sequence of shots ensuring visual variety and flow.
        """
        plans = []
        previous_move = None
        
        for i, (beat, duration) in enumerate(zip(beats, durations)):
            plan = self.plan_shot(beat, duration, previous_move)
            plans.append(plan)
            previous_move = plan.camera_move
        
        return plans
    
    def get_transition_recommendation(
        self, 
        current_emotion: Emotion, 
        next_emotion: Emotion
    ) -> str:
        """
        Recommend a transition type based on emotional shift.
        """
        # Same emotion: cut
        if current_emotion == next_emotion:
            return "cut"
        
        # Calm to intense: quick cut
        calm_emotions = {Emotion.CALM, Emotion.NEUTRAL, Emotion.MELANCHOLY}
        intense_emotions = {Emotion.INTENSE, Emotion.EPIC, Emotion.SUSPENSE}
        
        if current_emotion in calm_emotions and next_emotion in intense_emotions:
            return "cut"
        
        # Intense to calm: dissolve
        if current_emotion in intense_emotions and next_emotion in calm_emotions:
            return "dissolve"
        
        # Default: fade
        return "fade"
