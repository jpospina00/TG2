from fastapi import APIRouter
from web import user, module, challenge, progress, conversation, message, feedback, ai, diagnostic, student_profile

api = APIRouter()

api.include_router(user.router, prefix="/users", tags=["Users"])
api.include_router(module.router, prefix="/modules", tags=["Modules"])
api.include_router(challenge.router, prefix="/challenges", tags=["Challenges"])
api.include_router(progress.router, prefix="/progress", tags=["Progress"])
api.include_router(conversation.router, prefix="/conversations", tags=["Conversations"])
api.include_router(message.router, prefix="/messages", tags=["Messages"])
api.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
api.include_router(ai.router, prefix="/ai", tags=["AI"])
api.include_router(diagnostic.router, prefix="/diagnostic", tags=["Diagnostic"])
api.include_router(student_profile.router, prefix="/students", tags=["Student Profile"])