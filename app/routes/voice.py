"""
Voice Route for Finance Companion Web App
Accepts audio files, transcribes with Whisper, parses with NLP, 
and returns structured data for confirmation.
"""
import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from app.dependencies import get_db, get_current_user
from app.models import User, Category, Goal, GoalStatus
from app.voice_client.nlp_parser import parse_text

router = APIRouter(prefix="/voice", tags=["Voice"])

# Global whisper model (lazy loaded)
_whisper_model = None


def get_whisper_model():
    """Lazy load Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        if not WHISPER_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Whisper is not installed. Please install with: pip install openai-whisper"
            )
        # Use 'small' model for better accuracy (matches terminal voice client)
        model_name = os.getenv("WHISPER_MODEL", "small")
        _whisper_model = whisper.load_model(model_name)
    return _whisper_model


class VoiceTranscriptionResponse(BaseModel):
    """Response from voice transcription."""
    success: bool
    transcribed_text: str
    parsed_data: dict
    message: Optional[str] = None
    
    class Config:
        from_attributes = True


class ConfirmVoiceRequest(BaseModel):
    """Request to confirm and save voice-parsed data."""
    type: str  # expense, income, goal, contribution
    amount: float
    # Expense fields
    title: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    # Income fields
    source: Optional[str] = None
    # Goal fields
    savings_rate: Optional[float] = 0.20
    # Contribution fields
    goal_id: Optional[int] = None
    goal_name: Optional[str] = None
    # Common
    date: Optional[str] = None


@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe audio file and parse into structured financial data.
    
    Accepts audio files (wav, webm, mp3, ogg, m4a).
    Returns parsed data that can be edited before confirmation.
    """
    # Validate file type
    allowed_extensions = ['.wav', '.webm', '.mp3', '.ogg', '.m4a', '.mp4', '.mpeg', '.mpga']
    file_ext = os.path.splitext(audio.filename or '')[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save to temp file
    temp_path = None
    try:
        # Create temp file with proper extension
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tf:
            temp_path = tf.name
            content = await audio.read()
            tf.write(content)
        
        # Load Whisper model and transcribe
        model = get_whisper_model()
        result = model.transcribe(temp_path, language='en')
        transcribed_text = result.get("text", "").strip()
        
        if not transcribed_text:
            return VoiceTranscriptionResponse(
                success=False,
                transcribed_text="",
                parsed_data={},
                message="Could not transcribe audio. Please speak clearly and try again."
            )
        
        # Parse the transcribed text
        parsed = parse_text(transcribed_text)
        
        if parsed.get("error"):
            return VoiceTranscriptionResponse(
                success=False,
                transcribed_text=transcribed_text,
                parsed_data=parsed,
                message=parsed["error"]
            )
        
        # Enhance parsed data with category ID lookup
        if parsed.get("type") == "expense" and parsed.get("category"):
            category = db.query(Category).filter(
                Category.user_id == current_user.id,
                Category.name.ilike(parsed["category"])
            ).first()
            if category:
                parsed["category_id"] = category.id
                parsed["category_name"] = category.name
        
        # Enhance with goal ID lookup for contributions
        if parsed.get("type") == "contribution" and parsed.get("goal_name"):
            goal = db.query(Goal).filter(
                Goal.user_id == current_user.id,
                Goal.status == GoalStatus.active,
                Goal.title.ilike(f"%{parsed['goal_name']}%")
            ).first()
            if goal:
                parsed["goal_id"] = goal.id
                parsed["goal_title"] = goal.title
        
        # Get available categories for the user
        categories = db.query(Category).filter(
            Category.user_id == current_user.id
        ).all()
        parsed["available_categories"] = [
            {"id": c.id, "name": c.name} for c in categories
        ]
        
        # Get available goals for contributions
        if parsed.get("type") == "contribution":
            goals = db.query(Goal).filter(
                Goal.user_id == current_user.id,
                Goal.status == GoalStatus.active
            ).all()
            parsed["available_goals"] = [
                {"id": g.id, "title": g.title} for g in goals
            ]
        
        return VoiceTranscriptionResponse(
            success=True,
            transcribed_text=transcribed_text,
            parsed_data=parsed,
            message="Audio transcribed and parsed successfully!"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio: {str(e)}"
        )
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


@router.get("/status")
async def voice_status():
    """Check if voice transcription is available."""
    return {
        "whisper_available": WHISPER_AVAILABLE,
        "model": os.getenv("WHISPER_MODEL", "small") if WHISPER_AVAILABLE else None,
        "message": "Voice transcription ready" if WHISPER_AVAILABLE else "Whisper not installed"
    }
