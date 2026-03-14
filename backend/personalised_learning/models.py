from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String) 
    role = Column(String)      
    class_level = Column(String, nullable=True) 
    progress = relationship("Progress", back_populates="student", uselist=False)

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    accuracy = Column(Float, default=0.0)
    chapters_completed = Column(Integer, default=0)
    
    subject_mastery = Column(String, default='{"Math": 0, "Science": 0, "English": 0, "Hindi": 0, "Social Science": 0}')
    recent_activity = Column(String, default='[]')
    
    student = relationship("User", back_populates="progress")