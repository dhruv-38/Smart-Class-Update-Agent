from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Assignment(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class Announcement(BaseModel):
    id: str
    title: str
    content: str
    created_at: datetime

class CalendarEvent(BaseModel):
    summary: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    location: Optional[str] = None

class User(BaseModel):
    email: str
    name: str
    classroom_id: str