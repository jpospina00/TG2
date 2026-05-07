# stats.py
# Propósito: Endpoints de estadísticas y logros del usuario
# Dependencias: fastapi, sqlmodel
# Fecha: 2026-05-06

import json
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from model.challenge import Challenge
from model.conversation import Conversation
from model.feedback import Feedback
from model.progress import Progress
from model.diagnostic import Diagnostic
from model.student_profile import StudentProfile

router = APIRouter(tags=["Stats"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_completed_conversations(user_id: int, db: Session, module_name: str = None):
    """Retorna conversaciones con feedback completado, opcionalmente filtradas por módulo."""
    query = (
        select(Conversation, Feedback, Challenge)
        .join(Feedback, Feedback.conversation_id == Conversation.id)
        .join(Challenge, Challenge.id == Conversation.challenge_id)
        .where(
            Conversation.user_id == user_id,
            Feedback.completed == True
        )
    )
    results = db.exec(query).all()

    if module_name and module_name != "todos":
        from model.module import Module
        filtered = []
        for conv, fb, ch in results:
            mod = db.get(Module, ch.module_id)
            if mod and mod.name == module_name:
                filtered.append((conv, fb, ch))
        return filtered

    return results


def _get_all_conversations(user_id: int, db: Session, module_name: str = None):
    """Retorna todas las conversaciones con feedback."""
    query = (
        select(Conversation, Feedback, Challenge)
        .join(Feedback, Feedback.conversation_id == Conversation.id)
        .join(Challenge, Challenge.id == Conversation.challenge_id)
        .where(Conversation.user_id == user_id)
    )
    results = db.exec(query).all()

    if module_name and module_name != "todos":
        from model.module import Module
        filtered = []
        for conv, fb, ch in results:
            mod = db.get(Module, ch.module_id)
            if mod and mod.name == module_name:
                filtered.append((conv, fb, ch))
        return filtered

    return results


def _calculate_streak(conversations) -> int:
    """Calcula la racha actual de días consecutivos con al menos un reto."""
    if not conversations:
        return 0

    dates = set()
    for conv, fb, ch in conversations:
        if conv.started_at:
            dates.add(conv.started_at.date())

    if not dates:
        return 0

    today = datetime.utcnow().date()
    streak = 0
    current = today

    # Si no hizo nada hoy, empezar desde ayer
    if current not in dates:
        current = today - timedelta(days=1)

    while current in dates:
        streak += 1
        current -= timedelta(days=1)

    return streak


def _calculate_avg_time(conversations) -> dict:
    """Calcula tiempo promedio por tipo de reto en segundos."""
    times_by_type = defaultdict(list)

    for conv, fb, ch in conversations:
        if conv.started_at and conv.ended_at:
            duration = (conv.ended_at - conv.started_at).total_seconds()
            if 10 < duration < 3600:  # entre 10 segundos y 1 hora
                times_by_type[ch.type].append(duration)

    result = {}
    for rtype, times in times_by_type.items():
        if times:
            result[rtype] = round(sum(times) / len(times))

    return result


def _calculate_approval_by_level(all_convs) -> dict:
    """Calcula tasa de aprobación por nivel."""
    by_level = defaultdict(lambda: {"total": 0, "approved": 0})

    for conv, fb, ch in all_convs:
        level = ch.level
        by_level[level]["total"] += 1
        if fb.completed:
            by_level[level]["approved"] += 1

    result = {}
    for level, data in by_level.items():
        if data["total"] > 0:
            result[level] = round(data["approved"] / data["total"] * 100)
        else:
            result[level] = 0

    return result


def _calculate_empathy_dimensions(completed_convs) -> dict:
    """Calcula promedio de dimensiones de empatía desde feedback JSON."""
    dims = defaultdict(list)

    for conv, fb, ch in completed_convs:
        if ch.type == "analysis":
            try:
                data = json.loads(fb.content)
                scores = data.get("scores", {})
                for key in ["precision_emocional", "calidad_mensaje", "tono_empatico", "coherencia_contextual"]:
                    if key in scores:
                        dims[key].append(scores[key])
            except Exception:
                pass

    result = {}
    for key, values in dims.items():
        if values:
            result[key] = round(sum(values) / len(values), 1)

    return result


def _calculate_consecutive_approved(all_convs) -> int:
    """Calcula la racha actual de retos aprobados consecutivos."""
    sorted_convs = sorted(all_convs, key=lambda x: x[0].started_at or datetime.min)

    streak = 0
    for conv, fb, ch in reversed(sorted_convs):
        if fb.completed:
            streak += 1
        else:
            break

    return streak


def _get_best_empathy_score(completed_convs) -> float:
    """Retorna el mejor puntaje promedio en un reto de análisis."""
    best = 0.0

    for conv, fb, ch in completed_convs:
        if ch.type == "analysis":
            try:
                data = json.loads(fb.content)
                scores = data.get("scores", {})
                vals = [v for v in scores.values() if isinstance(v, (int, float))]
                if vals:
                    avg = sum(vals) / len(vals)
                    best = max(best, avg)
            except Exception:
                pass

    return round(best, 1)


def _format_seconds(seconds: int) -> str:
    """Formatea segundos a string legible."""
    if seconds < 60:
        return f"{seconds}s"
    m = seconds // 60
    s = seconds % 60
    if s == 0:
        return f"{m}m"
    return f"{m}m {s}s"


# ── Endpoint de estadísticas ───────────────────────────────────────────────────

@router.get("/stats/user/{user_id}")
def get_user_stats(user_id: int, module: str = "todos", db: Session = Depends(get_session)):
    """Retorna estadísticas completas del usuario, opcionalmente filtradas por módulo."""

    all_convs = _get_all_conversations(user_id, db, module)
    completed_convs = [(c, f, ch) for c, f, ch in all_convs if f.completed]

    total_attempts = len(all_convs)
    total_completed = len(completed_convs)
    approval_rate = round(total_completed / total_attempts * 100) if total_attempts > 0 else 0

    # Tiempo total en sesiones activas
    total_seconds = 0
    for conv, fb, ch in all_convs:
        if conv.started_at and conv.ended_at:
            dur = (conv.ended_at - conv.started_at).total_seconds()
            if 10 < dur < 3600:
                total_seconds += dur

    total_hours = int(total_seconds // 3600)
    total_minutes = int((total_seconds % 3600) // 60)

    if total_hours > 0:
        total_time_str = f"{total_hours}h {total_minutes}m"
    else:
        total_time_str = f"{total_minutes}m"

    # Racha — usa todas las conversaciones independiente del filtro
    all_convs_for_streak = _get_all_conversations(user_id, db)
    streak = _calculate_streak(all_convs_for_streak)

    # Progreso
    progress_records = db.exec(
        select(Progress).where(Progress.user_id == user_id)
    ).all()
    levels_unlocked = len([p for p in progress_records if p.current_level != "beginner"])

    # Tiempo por tipo
    avg_times = _calculate_avg_time(all_convs)
    avg_times_formatted = {k: _format_seconds(v) for k, v in avg_times.items()}

    # Aprobación por nivel
    approval_by_level = _calculate_approval_by_level(all_convs)

    # Dimensiones empatía
    empathy_dims = {}
    if module in ("todos", "empathy"):
        empathy_all = _get_all_conversations(user_id, db, "empathy")
        empathy_completed = [(c, f, ch) for c, f, ch in empathy_all if f.completed]
        empathy_dims = _calculate_empathy_dimensions(empathy_completed)

    return {
        "total_attempts": total_attempts,
        "total_completed": total_completed,
        "approval_rate": approval_rate,
        "total_time": total_time_str,
        "streak_days": streak,
        "levels_unlocked": levels_unlocked,
        "avg_time_by_type": avg_times_formatted,
        "approval_by_level": approval_by_level,
        "empathy_dimensions": empathy_dims,
    }


# ── Endpoint de logros ─────────────────────────────────────────────────────────

@router.get("/achievements/user/{user_id}")
def get_user_achievements(user_id: int, db: Session = Depends(get_session)):
    """Retorna los 15 logros del usuario con estado y progreso."""

    all_convs = _get_all_conversations(user_id, db)
    completed_convs = [(c, f, ch) for c, f, ch in all_convs if f.completed]
    total_completed = len(completed_convs)

    streak = _calculate_streak(all_convs)
    consecutive = _calculate_consecutive_approved(all_convs)
    best_score = _get_best_empathy_score(completed_convs)

    # Diagnósticos completados
    diagnostics = db.exec(
        select(Diagnostic).where(Diagnostic.user_id == user_id)
    ).all()
    has_diagnostic = len(diagnostics) > 0

    # Perfil completado
    profile = db.exec(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    ).first()
    has_profile = profile is not None

    # Retos en un mismo día
    days = defaultdict(int)
    for conv, fb, ch in completed_convs:
        if conv.started_at:
            days[conv.started_at.date()] += 1
    max_in_day = max(days.values()) if days else 0

    # Niveles por módulo
    progress_records = db.exec(
        select(Progress).where(Progress.user_id == user_id)
    ).all()

    from model.module import Module
    level_by_module = {}
    for p in progress_records:
        mod = db.get(Module, p.module_id)
        if mod:
            level_by_module[mod.name] = p.current_level

    empathy_level = level_by_module.get("empathy", "beginner")
    networking_level = level_by_module.get("networking", "beginner")
    levels_order = ["beginner", "intermediate", "advanced"]

    empathy_level_idx = levels_order.index(empathy_level)
    networking_level_idx = levels_order.index(networking_level)
    any_level_up = empathy_level_idx > 0 or networking_level_idx > 0

    # Fecha de primer reto
    first_conv_date = None
    if completed_convs:
        first_conv = min(completed_convs, key=lambda x: x[0].started_at or datetime.max)
        first_conv_date = first_conv[0].started_at.strftime("%d/%m/%Y") if first_conv[0].started_at else None

    def unlocked_date(convs_list, condition_fn):
        """Encuentra la fecha aproximada en que se desbloqueó un logro."""
        for conv, fb, ch in sorted(convs_list, key=lambda x: x[0].started_at or datetime.min):
            if condition_fn(conv, fb, ch):
                return conv.started_at.strftime("%d/%m/%Y") if conv.started_at else None
        return None

    achievements = [
        # ── Primeros pasos ──
        {
            "id": "first_challenge",
            "category": "Primeros pasos",
            "icon": "🎯",
            "color": "teal",
            "name": "Primer reto",
            "description": "Completaste tu primer desafío del sistema",
            "unlocked": total_completed >= 1,
            "unlocked_date": first_conv_date if total_completed >= 1 else None,
            "progress": min(total_completed, 1),
            "goal": 1,
        },
        {
            "id": "first_diagnostic",
            "category": "Primeros pasos",
            "icon": "🧪",
            "color": "blue",
            "name": "Diagnosticado",
            "description": "Completaste el diagnóstico inicial de un módulo",
            "unlocked": has_diagnostic,
            "unlocked_date": diagnostics[0].created_at.strftime("%d/%m/%Y") if has_diagnostic and diagnostics[0].created_at else None,
            "progress": 1 if has_diagnostic else 0,
            "goal": 1,
        },
        {
            "id": "profile_complete",
            "category": "Primeros pasos",
            "icon": "📝",
            "color": "purple",
            "name": "Perfil completo",
            "description": "Configuraste tu perfil académico en el onboarding",
            "unlocked": has_profile,
            "unlocked_date": profile.created_at.strftime("%d/%m/%Y") if has_profile and hasattr(profile, 'created_at') and profile.created_at else None,
            "progress": 1 if has_profile else 0,
            "goal": 1,
        },
        # ── Constancia ──
        {
            "id": "streak_3",
            "category": "Constancia",
            "icon": "🔥",
            "color": "gold",
            "name": "3 días seguidos",
            "description": "Completa al menos un reto por 3 días consecutivos",
            "unlocked": streak >= 3,
            "unlocked_date": None,
            "progress": min(streak, 3),
            "goal": 3,
        },
        {
            "id": "double_day",
            "category": "Constancia",
            "icon": "⚡",
            "color": "teal",
            "name": "Doble turno",
            "description": "Completa 2 retos aprobados en un mismo día",
            "unlocked": max_in_day >= 2,
            "unlocked_date": None,
            "progress": min(max_in_day, 2),
            "goal": 2,
        },
        {
            "id": "streak_7",
            "category": "Constancia",
            "icon": "🏆",
            "color": "gold",
            "name": "7 días seguidos",
            "description": "Completa al menos un reto por 7 días consecutivos",
            "unlocked": streak >= 7,
            "unlocked_date": None,
            "progress": min(streak, 7),
            "goal": 7,
        },
        # ── Hitos de retos ──
        {
            "id": "approved_5",
            "category": "Hitos de retos",
            "icon": "✨",
            "color": "bronze",
            "name": "5 aprobados",
            "description": "Aprueba un total de 5 retos en el sistema",
            "unlocked": total_completed >= 5,
            "unlocked_date": None,
            "progress": min(total_completed, 5),
            "goal": 5,
        },
        {
            "id": "approved_10",
            "category": "Hitos de retos",
            "icon": "🎖️",
            "color": "silver",
            "name": "10 aprobados",
            "description": "Aprueba un total de 10 retos en el sistema",
            "unlocked": total_completed >= 10,
            "unlocked_date": None,
            "progress": min(total_completed, 10),
            "goal": 10,
        },
        {
            "id": "approved_25",
            "category": "Hitos de retos",
            "icon": "💎",
            "color": "blue",
            "name": "25 aprobados",
            "description": "Aprueba un total de 25 retos en el sistema",
            "unlocked": total_completed >= 25,
            "unlocked_date": None,
            "progress": min(total_completed, 25),
            "goal": 25,
        },
        # ── Progresión ──
        {
            "id": "level_up",
            "category": "Progresión",
            "icon": "🚀",
            "color": "gold",
            "name": "Nivel superior",
            "description": "Sube de nivel en cualquier módulo del sistema",
            "unlocked": any_level_up,
            "unlocked_date": None,
            "progress": 1 if any_level_up else 0,
            "goal": 1,
        },
        {
            "id": "empathy_advanced",
            "category": "Progresión",
            "icon": "🧠",
            "color": "teal",
            "name": "Empático avanzado",
            "description": "Alcanza el nivel avanzado en el módulo de empatía",
            "unlocked": empathy_level == "advanced",
            "unlocked_date": None,
            "progress": empathy_level_idx,
            "goal": 2,
            "progress_label": f"Nivel {empathy_level} — {'¡completado!' if empathy_level == 'advanced' else f'falta {'1 nivel' if empathy_level == 'intermediate' else '2 niveles'}'}",
        },
        {
            "id": "networking_advanced",
            "category": "Progresión",
            "icon": "🤝",
            "color": "blue",
            "name": "Networker experto",
            "description": "Alcanza el nivel avanzado en el módulo de networking",
            "unlocked": networking_level == "advanced",
            "unlocked_date": None,
            "progress": networking_level_idx,
            "goal": 2,
            "progress_label": f"Nivel {networking_level} — {'¡completado!' if networking_level == 'advanced' else f'falta {'1 nivel' if networking_level == 'intermediate' else '2 niveles'}'}",
        },
        # ── Excelencia ──
        {
            "id": "perfect_score",
            "category": "Excelencia",
            "icon": "💫",
            "color": "gold",
            "name": "Puntaje perfecto",
            "description": "Obtén promedio ≥ 9.0 en un reto de análisis de empatía",
            "unlocked": best_score >= 9.0,
            "unlocked_date": None,
            "progress_label": f"Mejor puntaje: {best_score}" if best_score > 0 else "Sin intentos de análisis aún",
            "progress": min(int(best_score * 10), 90),
            "goal": 90,
        },
        {
            "id": "perfect_streak",
            "category": "Excelencia",
            "icon": "🎯",
            "color": "purple",
            "name": "Racha perfecta",
            "description": "Aprueba 5 retos consecutivos sin fallar ninguno",
            "unlocked": consecutive >= 5,
            "unlocked_date": None,
            "progress": min(consecutive, 5),
            "goal": 5,
        },
        {
            "id": "master_complete",
            "category": "Excelencia",
            "icon": "🏅",
            "color": "gold",
            "name": "Maestro completo",
            "description": "Alcanza el nivel avanzado en ambos módulos",
            "unlocked": empathy_level == "advanced" and networking_level == "advanced",
            "unlocked_date": None,
            "progress": (1 if empathy_level == "advanced" else 0) + (1 if networking_level == "advanced" else 0),
            "goal": 2,
        },
    ]

    total_unlocked = len([a for a in achievements if a["unlocked"]])

    return {
        "total_unlocked": total_unlocked,
        "total": len(achievements),
        "streak_days": streak,
        "achievements": achievements,
    }