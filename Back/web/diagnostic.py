# diagnostic.py
# Propósito: Endpoints del test diagnóstico y generación de retos personalizados
# Dependencias: fastapi, sqlmodel, service/ai, model/diagnostic, model/challenge
# Fecha: 2026-04-26

import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel
from database import engine
from model.diagnostic import Diagnostic
from model.challenge import Challenge
from model.progress import Progress
from model.student_profile import StudentProfile
from service import ai as ai_service

router = APIRouter(tags=["Diagnostic"])

LEVELS_ORDER = ["beginner", "intermediate", "advanced"]


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
    """Genera preguntas y escenario del diagnóstico en paralelo."""
    try:
        questions, scenario = await asyncio.gather(
            ai_service.generate_diagnostic_questions(module_name),
            ai_service.generate_diagnostic_scenario(module_name),
        )
        return {"questions": questions["questions"], "scenario": scenario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando diagnóstico: {str(e)}")


async def generate_and_save_challenges(
    req: SubmitDiagnosticRequest,
    evaluation: dict,
    student_profile_dict: dict,
):
    """Tarea en segundo plano — genera y guarda los retos personalizados."""
    try:
        level_result = evaluation["level_result"]
        assigned_index = LEVELS_ORDER.index(level_result)
        all_levels = LEVELS_ORDER[:assigned_index + 1]

        all_results = await asyncio.gather(*[
            ai_service.generate_personalized_challenges(
                module_name=req.module_name,
                level=level,
                user_id=req.user_id,
                diagnostic=evaluation,
                count=5,
                student_profile=student_profile_dict,
            )
            for level in all_levels
        ])

        all_challenges_data = dict(zip(all_levels, all_results))

        with Session(engine) as db:
            try:
                # Limpiar retos anteriores
                old_challenges = db.exec(
                    select(Challenge).where(
                        Challenge.user_id == req.user_id,
                        Challenge.module_id == req.module_id
                    )
                ).all()
                for c in old_challenges:
                    db.delete(c)

                # Insertar todos los retos en batch
                for level, challenges in all_challenges_data.items():
                    for ch in challenges:
                        db.add(Challenge(
                            module_id=req.module_id,
                            user_id=req.user_id,
                            level=level,
                            type=ch["type"],
                            agent_profile=ch["agent_profile"],
                            context=ch["context"],
                            opening_message=ch["opening_message"],
                        ))

                db.commit()
                print(f"[BG] Retos generados para user {req.user_id}, módulo {req.module_id}")

            except Exception as db_err:
                db.rollback()
                print(f"[BG] Error guardando retos: {db_err}")

    except Exception as e:
        print(f"[BG] Error generando retos en segundo plano: {e}")


@router.post("/submit")
async def submit_diagnostic(req: SubmitDiagnosticRequest, background_tasks: BackgroundTasks):
    """Evalúa el diagnóstico y retorna resultado inmediatamente. Genera retos en segundo plano."""
    try:
        # 1. Evaluar con IA — única llamada bloqueante
        evaluation = await ai_service.evaluate_diagnostic_response(
            module_name=req.module_name,
            multiple_choice_score=req.multiple_choice_score,
            scenario=req.scenario,
            written_response=req.written_response,
        )

        # 2. Validar level_result
        level_result = evaluation.get("level_result", "beginner")
        if level_result not in LEVELS_ORDER:
            level_result = "beginner"
        evaluation["level_result"] = level_result

        # 3. Obtener perfil del estudiante
        with Session(engine) as db:
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

        # 4. Guardar diagnóstico y actualizar nivel en BD — rápido
        with Session(engine) as db:
            try:
                diagnostic = Diagnostic(
                    user_id=req.user_id,
                    module_id=req.module_id,
                    level_result=level_result,
                    multiple_choice_score=req.multiple_choice_score,
                    written_response=req.written_response,
                    written_feedback=evaluation["written_feedback"],
                    strengths=evaluation["strengths"],
                    weaknesses=evaluation["weaknesses"],
                )
                db.add(diagnostic)

                progress = db.exec(
                    select(Progress).where(
                        Progress.user_id == req.user_id,
                        Progress.module_id == req.module_id
                    )
                ).first()
                if progress:
                    progress.current_level = level_result
                    db.add(progress)

                db.commit()
            except Exception as db_err:
                db.rollback()
                raise db_err

        # 5. Generar retos en segundo plano — no bloquea la respuesta
        background_tasks.add_task(
            generate_and_save_challenges,
            req, evaluation, student_profile_dict
        )

        # 6. Retornar inmediatamente
        return {
            "level_result": level_result,
            "written_feedback": evaluation["written_feedback"],
            "strengths": evaluation["strengths"],
            "weaknesses": evaluation["weaknesses"],
            "justification": evaluation.get("justification", ""),
            "challenges_ready": False,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error procesando diagnóstico: {str(e)}")


@router.get("/challenges-ready/{user_id}/{module_id}")
async def check_challenges_ready(user_id: int, module_id: int):
    """Polling — verifica si los retos personalizados ya están listos."""
    with Session(engine) as db:
        count = db.exec(
            select(Challenge).where(
                Challenge.user_id == user_id,
                Challenge.module_id == module_id
            )
        ).all()
        return {"ready": len(count) > 0, "count": len(count)}


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
        try:
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
        except Exception as e:
            db.rollback()
            raise e

    return {"message": "Diagnóstico reiniciado correctamente"}