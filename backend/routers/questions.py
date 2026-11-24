
import random
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from routers.auth import get_current_user
import models

router = APIRouter()

QUESTION_BANK = [
    {"id": 1,  "domain": "Interview",    "text": "Tell me about a time you faced a challenge and how you resolved it."},
    {"id": 2,  "domain": "Interview",    "text": "Why did you choose your field of study?"},
    {"id": 3,  "domain": "Interview",    "text": "Describe a project you are proud of and explain your role in it."},
    {"id": 4,  "domain": "Interview",    "text": "How do you handle working under pressure or tight deadlines?"},
    {"id": 5,  "domain": "Viva",         "text": "Summarise the main contribution of your project or research in simple terms."},
    {"id": 6,  "domain": "Viva",         "text": "What are the limitations of your work and how would you address them?"},
    {"id": 7,  "domain": "Viva",         "text": "Explain your methodology to someone unfamiliar with your field."},
    {"id": 8,  "domain": "Communication","text": "Describe how your city or hometown has changed in the last ten years."},
    {"id": 9,  "domain": "Communication","text": "Explain a concept from your field to a complete non-expert."},
    {"id": 10, "domain": "Communication","text": "What skill do you think is most important for professional success, and why?"},
]


class QuestionOut(BaseModel):
    id: int
    domain: str
    text: str


@router.get("/", response_model=List[QuestionOut])
def get_all_questions(current_user: models.User = Depends(get_current_user)):
    return QUESTION_BANK


@router.get("/random", response_model=List[QuestionOut])
def get_random_questions(current_user: models.User = Depends(get_current_user)):
    """Returns 4 randomly selected questions for a session."""
    return random.sample(QUESTION_BANK, 4)
