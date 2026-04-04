# diagnostic.py
# Propósito: Endpoints del test diagnóstico y generación de retos personalizados
# Dependencias: fastapi, sqlmodel, service/ai, model/diagnostic, model/challenge
# Fecha: 2026-03-20

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from database import engine
from model.diagnostic import Diagnostic
from model.challenge import Challenge
from model.progress import Progress
from model.student_profile import StudentProfile
from service import ai as ai_service

router = APIRouter(tags=["Diagnostic"])


class StartDiagnosticRequest(BaseModel):
    user_id: int
    module_id: int
    module_name: str


class SubmitDiagnosticRequest(BaseModel):
    user_id: int
    module_id: int
    module_name: str
    multiple_choice_score: int
    scenario: dict
    written_response: str


@router.get("/questions/{module_name}")
async def get_diagnostic_questions(module_name: str):
    """Genera las preguntas de opción múltiple para el diagnóstico."""
    try:
        questions = await ai_service.generate_diagnostic_questions(module_name)
        scenario = await ai_service.generate_diagnostic_scenario(module_name)
        return {"questions": questions["questions"], "scenario": scenario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando diagnóstico: {str(e)}")


@router.post("/submit")
async def submit_diagnostic(req: SubmitDiagnosticRequest):
    """Evalúa el diagnóstico y genera retos personalizados."""
    try:
        # 1. Evaluar con IA (fuera de la sesión DB)
        evaluation = await ai_service.evaluate_diagnostic_response(
            module_name=req.module_name,
            multiple_choice_score=req.multiple_choice_score,
            scenario=req.scenario,
            written_response=req.written_response,
        )

        # 2. Generar retos para niveles anteriores (fuera de sesión DB)
        levels_order = ["beginner", "intermediate", "advanced"]
        assigned_index = levels_order.index(evaluation["level_result"])
        lower_challenges_data = {}

        # 3. Guardar todo en BD
        with Session(engine) as db:
            # Obtener perfil del estudiante
            student_prof = db.exec(
                select(StudentProfile).where(StudentProfile.user_id == req.user_id)
            ).first()

            student_profile_dict = None
            if student_prof:
                student_profile_dict = {
                    "has_profile": True,
                    "semester": student_prof.semester,
                    "specialization": student_prof.specialization,
                    "self_assessed_level": student_prof.self_assessed_level,
                }

        # 4. Generar retos del nivel asignado con perfil
        challenges_data = await ai_service.generate_personalized_challenges(
            module_name=req.module_name,
            level=evaluation["level_result"],
            user_id=req.user_id,
            diagnostic=evaluation,
            count=5,
            student_profile=student_profile_dict,
        )

        # 5. Generar retos para niveles anteriores con perfil
        for lower_level in levels_order[:assigned_index]:
            lower_challenges_data[lower_level] = await ai_service.generate_personalized_challenges(
                module_name=req.module_name,
                level=lower_level,
                user_id=req.user_id,
                diagnostic=evaluation,
                count=5,
                student_profile=student_profile_dict,
            )

        # 6. Guardar todo en BD
        with Session(engine) as db:
            # Limpiar retos personalizados anteriores
            old_challenges = db.exec(
                select(Challenge).where(
                    Challenge.user_id == req.user_id,
                    Challenge.module_id == req.module_id
                )
            ).all()
            for c in old_challenges:
                db.delete(c)
            db.commit()

            # Guardar diagnóstico
            diagnostic = Diagnostic(
                user_id=req.user_id,
                module_id=req.module_id,
                level_result=evaluation["level_result"],
                multiple_choice_score=req.multiple_choice_score,
                written_response=req.written_response,
                written_feedback=evaluation["written_feedback"],
                strengths=evaluation["strengths"],
                weaknesses=evaluation["weaknesses"],
            )
            db.add(diagnostic)
            db.commit()
            db.refresh(diagnostic)

            # Actualizar nivel del usuario
            progress = db.exec(
                select(Progress).where(
                    Progress.user_id == req.user_id,
                    Progress.module_id == req.module_id
                )
            ).first()
            if progress:
                progress.current_level = evaluation["level_result"]
                db.add(progress)
                db.commit()

            # Guardar retos del nivel asignado
            saved_challenges = []
            for ch in challenges_data:
                challenge = Challenge(
                    module_id=req.module_id,
                    user_id=req.user_id,
                    level=evaluation["level_result"],
                    type=ch["type"],
                    agent_profile=ch["agent_profile"],
                    context=ch["context"],
                    opening_message=ch["opening_message"],
                )
                db.add(challenge)
                db.commit()
                db.refresh(challenge)
                saved_challenges.append(challenge)

            # Guardar retos de niveles anteriores
            for lower_level, lower_chs in lower_challenges_data.items():
                for ch in lower_chs:
                    challenge = Challenge(
                        module_id=req.module_id,
                        user_id=req.user_id,
                        level=lower_level,
                        type=ch["type"],
                        agent_profile=ch["agent_profile"],
                        context=ch["context"],
                        opening_message=ch["opening_message"],
                    )
                    db.add(challenge)
                    db.commit()
                    db.refresh(challenge)
                    saved_challenges.append(challenge)

        return {
            "level_result": evaluation["level_result"],
            "written_feedback": evaluation["written_feedback"],
            "strengths": evaluation["strengths"],
            "weaknesses": evaluation["weaknesses"],
            "justification": evaluation["justification"],
            "challenges_generated": len(saved_challenges),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error procesando diagnóstico: {str(e)}")


@router.get("/user/{user_id}/module/{module_id}")
async def get_user_diagnostic(user_id: int, module_id: int):
    """Obtiene el último diagnóstico de un usuario para un módulo."""
    with Session(engine) as db:
        diagnostics = db.exec(
            select(Diagnostic).where(
                Diagnostic.user_id == user_id,
                Diagnostic.module_id == module_id
            ).order_by(Diagnostic.created_at.desc())
        ).all()

        if not diagnostics:
            return {"has_diagnostic": False}

        latest = diagnostics[0]
        return {
            "has_diagnostic": True,
            "level_result": latest.level_result,
            "written_feedback": latest.written_feedback,
            "strengths": latest.strengths,
            "weaknesses": latest.weaknesses,
            "created_at": latest.created_at,
            "total_diagnostics": len(diagnostics),
        }


@router.delete("/user/{user_id}/module/{module_id}/reset")
async def reset_diagnostic(user_id: int, module_id: int):
    """Elimina el diagnóstico y retos personalizados para repetir el test."""
    with Session(engine) as db:
        diagnostics = db.exec(
            select(Diagnostic).where(
                Diagnostic.user_id == user_id,
                Diagnostic.module_id == module_id
            )
        ).all()
        for d in diagnostics:
            db.delete(d)

        challenges = db.exec(
            select(Challenge).where(
                Challenge.user_id == user_id,
                Challenge.module_id == module_id
            )
        ).all()
        for c in challenges:
            db.delete(c)

        progress = db.exec(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.module_id == module_id
            )
        ).first()
        if progress:
            progress.current_level = "beginner"
            db.add(progress)

        db.commit()

    return {"message": "Diagnóstico reiniciado correctamente"}