from pydantic import BaseModel

class PerformanceCreate(BaseModel):
    student_id: int
    subject: str
    chapter: str
    quiz_score: float
    doubts_asked: int
