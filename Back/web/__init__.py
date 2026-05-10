from fastapi import APIRouter, Depends
from web import user, module, challenge, progress, conversation, message, feedback, ai, diagnostic, student_profile, stats
from utils.auth import get_current_user

api = APIRouter()

# Rutas públicas — no requieren autenticación
api.include_router(user.router,           prefix="/users",         tags=["Users"])

# Rutas protegidas — todas requieren JWT válido de Auth0
_auth = [Depends(get_current_user)]

api.include_router(module.router,         prefix="/modules",       tags=["Modules"],          dependencies=_auth)
api.include_router(challenge.router,      prefix="/challenges",    tags=["Challenges"],        dependencies=_auth)
api.include_router(progress.router,       prefix="/progress",      tags=["Progress"],          dependencies=_auth)
api.include_router(conversation.router,   prefix="/conversations", tags=["Conversations"],     dependencies=_auth)
api.include_router(message.router,        prefix="/messages",      tags=["Messages"],          dependencies=_auth)
api.include_router(feedback.router,       prefix="/feedback",      tags=["Feedback"],          dependencies=_auth)
api.include_router(ai.router,             prefix="/ai",            tags=["AI"],                dependencies=_auth)
api.include_router(diagnostic.router,     prefix="/diagnostic",    tags=["Diagnostic"],        dependencies=_auth)
api.include_router(student_profile.router,prefix="/students",      tags=["Student Profile"],   dependencies=_auth)
api.include_router(stats.router,          prefix="",              tags=["Stats"],             dependencies=_auth)