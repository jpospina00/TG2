# ai.py
# Propósito: Router de IA — evaluación, retos conversacionales y avance de nivel
# Dependencias: fastapi, sqlmodel, service/ai
# Fecha: 2026-03-20

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime

from database import get_session
from model.challenge import Challenge
from model.conversation import Conversation
from model.message import Message
from model.feedback import Feedback
from model.progress import Progress
from model.module import Module
from service.ai import (
    evaluate_simple_response,
    generate_agent_reply,
    evaluate_conversation,
    generate_new_challenge
)
from service import message as message_service

router = APIRouter()

LEVELS_ORDER = ["beginner", "intermediate", "advanced"]
CHALLENGES_TO_PASS = 4


class SimpleSubmit(BaseModel):
    conversation_id: int
    student_response: str


class ConversationalTurn(BaseModel):
    conversation_id: int
    student_message: str
    history: list[dict]


class CloseConversation(BaseModel):
    conversation_id: int
    history: list[dict]


class GetOrCreateChallenge(BaseModel):
    user_id: int
    module_id: int
    level: str


@router.post("/simple/evaluate")
async def evaluate_simple(payload: SimpleSubmit, db: Session = Depends(get_session)):
    conv = db.get(Conversation, payload.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    challenge = db.get(Challenge, conv.challenge_id)
    module = db.get(Module, challenge.module_id)

    last_order = db.exec(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.order.desc())
    ).first()
    next_order = (last_order.order + 1) if last_order else 2

    message_service.create_message(
        Message(
            conversation_id=conv.id,
            role="user",
            content=payload.student_response,
            order=next_order
        ), db
    )

    feedback_text, completed = evaluate_simple_response(
        module_name=module.name,
        level=challenge.level,
        agent_profile=challenge.agent_profile,
        context=challenge.context,
        opening_message=challenge.opening_message,
        student_response=payload.student_response
    )

    conv.ended_at = datetime.utcnow()
    db.add(conv)
    db.commit()

    new_feedback = Feedback(
        conversation_id=conv.id,
        content=feedback_text,
        completed=completed
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)

    level_up = await check_and_advance_level(conv.user_id, challenge.module_id, challenge.level, db)

    return {"feedback": feedback_text, "completed": completed, "level_up": level_up}


@router.post("/conversational/turn")
def conversational_turn(payload: ConversationalTurn, db: Session = Depends(get_session)):
    conv = db.get(Conversation, payload.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    challenge = db.get(Challenge, conv.challenge_id)
    module = db.get(Module, challenge.module_id)

    student_order = len(payload.history) + 1
    message_service.create_message(
        Message(
            conversation_id=conv.id,
            role="user",
            content=payload.student_message,
            order=student_order
        ), db
    )

    updated_history = payload.history + [{"role": "user", "content": payload.student_message}]
    agent_reply = generate_agent_reply(
        module_name=module.name,
        level=challenge.level,
        agent_profile=challenge.agent_profile,
        context=challenge.context,
        conversation_history=updated_history
    )

    message_service.create_message(
        Message(
            conversation_id=conv.id,
            role="agent",
            content=agent_reply,
            order=student_order + 1
        ), db
    )

    return {
        "agent_reply": agent_reply,
        "turn_count": len([m for m in updated_history if m["role"] == "user"])
    }


@router.post("/conversational/close")
async def close_conversational(payload: CloseConversation, db: Session = Depends(get_session)):
    conv = db.get(Conversation, payload.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    challenge = db.get(Challenge, conv.challenge_id)
    module = db.get(Module, challenge.module_id)

    feedback_text, completed = evaluate_conversation(
        module_name=module.name,
        level=challenge.level,
        agent_profile=challenge.agent_profile,
        context=challenge.context,
        conversation_history=payload.history
    )

    conv.ended_at = datetime.utcnow()
    db.add(conv)
    db.commit()

    new_feedback = Feedback(
        conversation_id=conv.id,
        content=feedback_text,
        completed=completed
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)

    level_up = await check_and_advance_level(conv.user_id, challenge.module_id, challenge.level, db)

    return {"feedback": feedback_text, "completed": completed, "level_up": level_up}


@router.post("/challenges/next")
def get_next_challenge(payload: GetOrCreateChallenge, db: Session = Depends(get_session)):
    completed_ids = db.exec(
        select(Conversation.challenge_id)
        .join(Feedback, Feedback.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == payload.user_id,
            Feedback.completed == True
        )
    ).all()

    available = db.exec(
        select(Challenge).where(
            Challenge.module_id == payload.module_id,
            Challenge.level == payload.level,
            Challenge.id.not_in(completed_ids) if completed_ids else Challenge.id != None
        )
    ).first()

    if available:
        return available

    module = db.get(Module, payload.module_id)
    challenge_type = "simple" if payload.level == "beginner" else "conversational"

    new_data = generate_new_challenge(
        module_name=module.name,
        level=payload.level,
        challenge_type=challenge_type
    )

    new_challenge = Challenge(
        module_id=payload.module_id,
        level=payload.level,
        type=challenge_type,
        agent_profile=new_data["agent_profile"],
        context=new_data["context"],
        opening_message=new_data["opening_message"]
    )
    db.add(new_challenge)
    db.commit()
    db.refresh(new_challenge)

    return new_challenge


async def check_and_advance_level(user_id: int, module_id: int, current_level: str, db: Session) -> bool:
    if current_level == "advanced":
        return False

    count = db.exec(
        select(Feedback)
        .join(Conversation, Conversation.id == Feedback.conversation_id)
        .join(Challenge, Challenge.id == Conversation.challenge_id)
        .where(
            Conversation.user_id == user_id,
            Challenge.module_id == module_id,
            Challenge.level == current_level,
            Feedback.completed == True
        )
    ).all()

    if len(count) >= CHALLENGES_TO_PASS:
        progress = db.exec(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.module_id == module_id
            )
        ).first()

        if progress:
            next_level_index = LEVELS_ORDER.index(current_level) + 1
            new_level = LEVELS_ORDER[next_level_index]
            progress.current_level = new_level
            progress.last_activity = datetime.utcnow()
            db.add(progress)
            db.commit()

            try:
                module = db.get(Module, module_id)

                from model.diagnostic import Diagnostic
                diagnostic_record = db.exec(
                    select(Diagnostic).where(
                        Diagnostic.user_id == user_id,
                        Diagnostic.module_id == module_id
                    ).order_by(Diagnostic.created_at.desc())
                ).first()

                diagnostic = {}
                if diagnostic_record:
                    diagnostic = {
                        "strengths": diagnostic_record.strengths,
                        "weaknesses": diagnostic_record.weaknesses,
                        "written_feedback": diagnostic_record.written_feedback,
                    }

                # Obtener perfil del estudiante
                from model.student_profile import StudentProfile
                student_prof = db.exec(
                    select(StudentProfile).where(StudentProfile.user_id == user_id)
                ).first()

                student_profile_dict = None
                if student_prof:
                    student_profile_dict = {
                        "has_profile": True,
                        "semester": student_prof.semester,
                        "specialization": student_prof.specialization,
                        "self_assessed_level": student_prof.self_assessed_level,
                    }

                from service.ai import generate_personalized_challenges
                challenges_data = await generate_personalized_challenges(
                    module_name=module.name,
                    level=new_level,
                    user_id=user_id,
                    diagnostic=diagnostic,
                    count=5,
                    student_profile=student_profile_dict,
                )

                for ch in challenges_data:
                    new_challenge = Challenge(
                        module_id=module_id,
                        user_id=user_id,
                        level=new_level,
                        type=ch["type"],
                        agent_profile=ch["agent_profile"],
                        context=ch["context"],
                        opening_message=ch["opening_message"],
                    )
                    db.add(new_challenge)
                db.commit()

            except Exception as e:
                print(f"Error generando retos para nuevo nivel: {e}")

            return True

    return False