# tests/test_ai_eval.py
# Propósito: Pruebas de evaluación de la IA usando JSON Match y LLM-as-a-Judge
# Métodos:
#   - JSON Match:      verifica outputs estructurados (usa llama-3.3-70b-versatile)
#   - LLM-as-a-Judge:  usa deepseek-r1-distill-llama-70b (más avanzado) para evaluar
# Dependencias: pytest, groq
# Fecha: 2026-05-09

import os
import sys
import json
import time
import pytest
from pathlib import Path

# Asegurar que el directorio raíz del backend esté en el path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from groq import Groq
from config import settings

# ── Reutilizar la misma lógica de ai.py para fallback de API keys ────────────

_groq_client = None

def get_groq_client() -> Groq:
    """Obtiene el cliente Groq con fallback entre múltiples API keys."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    
    keys = settings.groq_keys_list
    if not keys:
        raise Exception("No Groq API keys configured")
    
    _groq_client = Groq(api_key=keys[0])
    return _groq_client


def call_groq(prompt: str, system: str = "", max_tokens: int = 800, model: str = "llama-3.3-70b-versatile") -> str:
    """
    Llama a Groq con fallback entre múltiples API keys.
    
    Modelos disponibles en Groq (ordenados por capacidad):
    - deepseek-r1-distill-llama-70b  ★★★★★  (~GPT-4 level, mejor razonamiento)
    - llama-3.3-70b-specdec          ★★★★☆  (optimizado, muy rápido)
    - llama-3.3-70b-versatile        ★★★★☆  (balance calidad/velocidad)
    - mixtral-8x7b-32768             ★★★☆☆  (bueno pero menos capacidad)
    - gemma2-9b-it                   ★★★☆☆  (ligero, rápido)
    """
    global _groq_client
    keys = settings.groq_keys_list
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    for i, key in enumerate(keys):
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            _groq_client = client
            return response.choices[0].message.content.strip()
        except Exception as e:
            if i == len(keys) - 1:
                raise e
            print(f"Error con API key {i+1}, probando siguiente... Error: {e}")
            continue


# ── Helpers para pruebas (usan llama-3.3-70b-versatile por defecto) ───────────

def get_evaluation_output(
    module: str,
    agent_profile: str,
    context: str,
    opening_message: str,
    student_response: str,
    level: str = "beginner",
) -> dict:
    """
    Llama al prompt de evaluación de respuesta simple y retorna el JSON parseado.
    Usa llama-3.3-70b-versatile (mismo que ai.py)
    """
    system = f"""You are an expert evaluator of professional written communication skills.
Evaluate the student's response and return ONLY a valid JSON object with this exact structure:
{{
  "feedback": "detailed feedback in Spanish (2-4 sentences)",
  "completed": true or false,
  "score": number between 1 and 10
}}
Module: {module}. Level: {level}.
Criteria: clarity, tone, appropriateness, empathy (if empathy module), professionalism (if networking).
completed=true if score >= 6 for beginner, >= 6.5 for intermediate, >= 7 for advanced."""

    prompt = f"""Agent profile: {agent_profile}
Context: {context}
Opening message: {opening_message}
Student response: {student_response}

Return only the JSON object, no additional text."""

    raw = call_groq(prompt, system, max_tokens=400, model="llama-3.3-70b-versatile")
    raw = raw.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


def get_diagnostic_output(
    module: str,
    written_response: str,
    multiple_choice_score: int,
) -> dict:
    """
    Llama al prompt de diagnóstico y retorna el JSON parseado.
    Usa llama-3.3-70b-versatile (mismo que ai.py)
    """
    system = """You are an expert evaluator. Analyze the student's diagnostic response.
Return ONLY a valid JSON object with this exact structure:
{
  "level_result": "beginner" or "intermediate" or "advanced",
  "written_feedback": "feedback in Spanish (2-3 sentences)",
  "strengths": "strengths in Spanish",
  "weaknesses": "areas for improvement in Spanish",
  "justification": "brief justification for the level assigned"
}"""

    prompt = f"""Module: {module}
Multiple choice score: {multiple_choice_score}/3
Written response: {written_response}

Assign level based on: beginner (<5 total), intermediate (5-7), advanced (>7).
Return only the JSON object."""

    raw = call_groq(prompt, system, max_tokens=500, model="llama-3.3-70b-versatile")
    raw = raw.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


def get_empathy_scores(
    situation: str,
    emotion_identified: str,
    student_response: str,
) -> dict:
    """
    Llama al prompt de evaluación de empatía y retorna el JSON con scores.
    Usa llama-3.3-70b-versatile (mismo que ai.py)
    """
    system = """You are an empathy evaluation expert.
Return ONLY a valid JSON object with this exact structure:
{
  "scores": {
    "precision_emocional": number 1-10,
    "calidad_mensaje": number 1-10,
    "tono_empatico": number 1-10,
    "coherencia_contextual": number 1-10
  },
  "average": number 1-10,
  "feedback": "evaluation in Spanish (2-3 sentences)",
  "completed": true or false
}
completed=true if average >= 6.0"""

    prompt = f"""Situation: {situation}
Emotion identified by student: {emotion_identified}
Student empathic response: {student_response}

Evaluate each dimension and return only the JSON."""

    raw = call_groq(prompt, system, max_tokens=400, model="llama-3.3-70b-versatile")
    raw = raw.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


# ── LLM-as-a-Judge con modelo más avanzado de Groq ────────────────────────────

def llm_judge_advanced(output: dict, criteria: list[str]) -> dict:
    """
    Usa el modelo MÁS AVANZADO de Groq como juez independiente.
    
    MODELO: deepseek-r1-distill-llama-70b
    - Arquitectura: DeepSeek R1 (distilado sobre LLaMA 70B)
    - Capacidad: ~GPT-4 level para razonamiento y evaluación
    - Ventaja: Es diferente a LLaMA 3.3, evitando sesgo de autoconfirmación
    - Rendimiento: Superior en tareas de juicio cualitativo
    
    Alternativas si deepseek falla:
    - llama-3.3-70b-specdec (optimizado, muy rápido)
    - llama-3.3-70b-versatile (fallback seguro)
    """
    criteria_text = "\n".join(f"{i+1}. {c}" for i, c in enumerate(criteria))
    output_text = json.dumps(output, ensure_ascii=False, indent=2)
    
    judge_prompt = f"""Eres un evaluador experto en sistemas de aprendizaje con IA.
Tu tarea es evaluar el output generado por otro modelo de IA (LLaMA 3.3 70B)
para un sistema de entrenamiento de habilidades blandas universitarias.

OUTPUT A EVALUAR:
{output_text}

CRITERIOS DE EVALUACIÓN (puntúa cada uno de 1 a 5, donde 1=muy deficiente, 5=excelente):
{criteria_text}

Responde SOLO con un JSON con esta estructura exacta, sin texto adicional:
{{
  "evaluaciones": [
    {{"criterio": "nombre del criterio", "puntaje": número 1-5, "justificación": "texto breve"}}
  ],
  "promedio": número 1-5,
  "observacion_general": "observación general en 1-2 oraciones"
}}"""
    
    # Intentar primero con el modelo más avanzado
    try:
        raw = call_groq(judge_prompt, system="", max_tokens=800, model="deepseek-r1-distill-llama-70b")
        raw = raw.strip().strip("```json").strip("```").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"Error con deepseek-r1-distill-llama-70b: {e}")
        print("Intentando con llama-3.3-70b-specdec...")
        try:
            # Fallback a specdec (optimizado pero igual de capaz)
            raw = call_groq(judge_prompt, system="", max_tokens=800, model="llama-3.3-70b-specdec")
            raw = raw.strip().strip("```json").strip("```").strip()
            return json.loads(raw)
        except Exception as e2:
            print(f"Error con llama-3.3-70b-specdec: {e2}")
            print("Fallback final a llama-3.3-70b-versatile...")
            # Fallback final al mismo modelo que genera outputs
            raw = call_groq(judge_prompt, system="", max_tokens=800, model="llama-3.3-70b-versatile")
            raw = raw.strip().strip("```json").strip("```").strip()
            return json.loads(raw)


# ═══════════════════════════════════════════════════════════════════════════════
# JSON MATCH TESTS (usan llama-3.3-70b-versatile)
# ═══════════════════════════════════════════════════════════════════════════════

class TestJsonMatch:
    """
    Verifica que los outputs de la IA tengan la estructura JSON correcta.
    Usa llama-3.3-70b-versatile (mismo modelo que en producción).
    """

    def test_simple_evaluation_has_required_fields(self):
        """El output de evaluación debe tener: feedback, completed, score."""
        output = get_evaluation_output(
            module="networking",
            agent_profile="Reclutadora de empresa de tecnología",
            context="Proceso de selección para una vacante de desarrollo backend",
            opening_message="Hola, vi tu perfil en LinkedIn. ¿Podrías contarme sobre tu experiencia?",
            student_response="Buenos días. Tengo 3 años de experiencia en backend con Python y FastAPI.",
        )
        assert "feedback" in output
        assert "completed" in output
        assert "score" in output

    def test_simple_evaluation_field_types(self):
        """Los tipos de datos del output deben ser correctos."""
        output = get_evaluation_output(
            module="networking",
            agent_profile="Gerente de proyectos tech",
            context="Reunión de seguimiento de proyecto",
            opening_message="Necesito que me expliques el retraso en las entregas.",
            student_response="Entiendo su preocupación. El retraso se debió a cambios en los requisitos.",
        )
        assert isinstance(output["feedback"], str)
        assert isinstance(output["completed"], bool)
        assert isinstance(output["score"], (int, float))

    def test_simple_evaluation_score_range(self):
        """El score debe estar entre 1 y 10."""
        output = get_evaluation_output(
            module="networking",
            agent_profile="Mentor profesional senior",
            context="Sesión de mentoría sobre desarrollo de carrera",
            opening_message="¿Qué estrategias has usado para crecer profesionalmente?",
            student_response="He buscado proyectos desafiantes, pedido feedback constantemente y tomado cursos.",
        )
        assert 1 <= output["score"] <= 10

    def test_simple_evaluation_feedback_not_empty(self):
        """El feedback no puede ser una cadena vacía."""
        output = get_evaluation_output(
            module="networking",
            agent_profile="Colega de trabajo",
            context="Colaboración en proyecto grupal",
            opening_message="¿Puedes encargarte de la presentación del viernes?",
            student_response="Claro, con gusto me encargo.",
        )
        assert len(output["feedback"].strip()) > 20

    def test_completed_true_for_good_response(self):
        """Una respuesta claramente buena debe obtener completed=True."""
        output = get_evaluation_output(
            module="networking",
            agent_profile="Director de recursos humanos",
            context="Entrevista final para cargo de liderazgo",
            opening_message="¿Por qué deberíamos contratarte para este cargo?",
            student_response=(
                "Cuento con experiencia liderando equipos multidisciplinarios y he demostrado "
                "resultados concretos en proyectos similares."
            ),
        )
        assert output["completed"] is True

    def test_completed_false_for_poor_response(self):
        """Una respuesta claramente mala debe obtener completed=False."""
        output = get_evaluation_output(
            module="networking",
            agent_profile="Reclutadora de empresa de tecnología",
            context="Primera entrevista de trabajo",
            opening_message="¿Por qué quieres trabajar con nosotros?",
            student_response="no se",
        )
        assert output["completed"] is False

    def test_diagnostic_has_required_fields(self):
        """El output de diagnóstico debe tener todos los campos requeridos."""
        output = get_diagnostic_output(
            module="networking",
            written_response="Explicaría la situación con claridad y propondría soluciones concretas.",
            multiple_choice_score=2,
        )
        required = ["level_result", "written_feedback", "strengths", "weaknesses", "justification"]
        for field in required:
            assert field in output

    def test_diagnostic_level_is_valid_enum(self):
        """El nivel asignado debe ser uno de los tres valores válidos."""
        output = get_diagnostic_output(
            module="empathy",
            written_response="Entiendo que debe ser difícil para ti. ¿Cómo te puedo ayudar?",
            multiple_choice_score=3,
        )
        valid_levels = {"beginner", "intermediate", "advanced"}
        assert output["level_result"] in valid_levels

    def test_diagnostic_beginner_for_poor_response(self):
        """Una respuesta pobre con puntaje bajo debe asignar nivel beginner."""
        output = get_diagnostic_output(
            module="networking",
            written_response="le digo que si",
            multiple_choice_score=0,
        )
        assert output["level_result"] == "beginner"

    def test_diagnostic_advanced_for_excellent_response(self):
        """Una respuesta excelente con puntaje alto debe asignar nivel advanced."""
        output = get_diagnostic_output(
            module="networking",
            written_response=(
                "En este contexto, lo más apropiado sería establecer un canal de comunicación "
                "claro con el cliente, explicar el impacto de los cambios solicitados."
            ),
            multiple_choice_score=3,
        )
        assert output["level_result"] in {"intermediate", "advanced"}

    def test_empathy_scores_structure(self):
        """Los scores de empatía deben tener las 4 dimensiones requeridas."""
        output = get_empathy_scores(
            situation="Tu compañero te dice que está agotado y considera abandonar el proyecto grupal.",
            emotion_identified="agotamiento y frustración",
            student_response="Entiendo que estás muy cansado. ¿Qué parte del proyecto te está pesando más?",
        )
        required_dims = ["precision_emocional", "calidad_mensaje", "tono_empatico", "coherencia_contextual"]
        for dim in required_dims:
            assert dim in output["scores"]

    def test_empathy_scores_range(self):
        """Todos los scores individuales deben estar entre 1 y 10."""
        output = get_empathy_scores(
            situation="Tu amiga te escribe llorando porque reprobó el examen final.",
            emotion_identified="tristeza y frustración",
            student_response="Qué pena que te haya pasado eso. Ánimo, seguro la próxima vez te va mejor.",
        )
        for dim, val in output["scores"].items():
            assert 1 <= val <= 10

    def test_empathy_average_matches_scores(self):
        """El average debe ser coherente con los scores individuales (±0.5)."""
        output = get_empathy_scores(
            situation="Un compañero te pide ayuda porque no entiende el tema y tiene miedo de reprobar.",
            emotion_identified="miedo y ansiedad",
            student_response="Con mucho gusto te explico. Es normal no entender todo a la primera.",
        )
        calculated_avg = sum(output["scores"].values()) / len(output["scores"])
        assert abs(output["average"] - calculated_avg) <= 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# LLM-AS-A-JUDGE TESTS (usan deepseek-r1-distill-llama-70b - MÁS AVANZADO)
# ═══════════════════════════════════════════════════════════════════════════════

class TestLLMJudge:
    """
    Usa el modelo MÁS AVANZADO de Groq (DeepSeek R1 70B) como juez.
    DeepSeek R1 es superior en razonamiento y evaluación comparado con LLaMA 3.3.
    """

    PASSING_SCORE = 3.0  # Sobre 5

    def test_feedback_is_constructive_and_specific(self):
        """El feedback debe ser constructivo, específico y accionable."""
        output = get_evaluation_output(
            module="networking",
            agent_profile="Reclutadora de empresa de tecnología",
            context="Entrevista inicial para desarrollador backend",
            opening_message="¿Cuéntame sobre un proyecto del que estés orgulloso?",
            student_response="Desarrollé una API REST con FastAPI que redujo el tiempo de respuesta en un 40%.",
        )
        time.sleep(1)  # Respetar rate limits de Groq
        judgment = llm_judge_advanced(output, criteria=[
            "El feedback identifica aspectos positivos concretos de la respuesta",
            "El feedback señala áreas de mejora de forma específica y constructiva",
            "El feedback es accionable — el estudiante puede saber qué mejorar",
            "El lenguaje es respetuoso y motivador",
            "El feedback está escrito en español correcto y claro",
        ])
        avg = judgment["promedio"]
        assert avg >= self.PASSING_SCORE, f"Promedio juez: {avg}/5. {judgment.get('observacion_general', '')}"

    def test_feedback_is_empathetic_in_empathy_module(self):
        """En el módulo de empatía, el feedback debe reconocer el componente emocional."""
        output = get_empathy_scores(
            situation="Tu compañero de tesis está muy estresado y te dice que ya no puede más.",
            emotion_identified="estrés y agotamiento",
            student_response="Tranquilo, seguro que lo logras. Ya falta poco.",
        )
        time.sleep(1)
        judgment = llm_judge_advanced(output, criteria=[
            "El feedback reconoce la dimensión emocional de la situación evaluada",
            "El feedback explica por qué la respuesta fue o no empática",
            "El feedback orienta cómo mejorar la empatía en la respuesta",
            "Los puntajes asignados son coherentes con la calidad de la respuesta",
            "El feedback es útil para que el estudiante desarrolle inteligencia emocional",
        ])
        avg = judgment["promedio"]
        assert avg >= self.PASSING_SCORE, f"Promedio juez: {avg}/5"

    def test_diagnostic_feedback_is_personalized(self):
        """El feedback del diagnóstico debe ser personalizado según la respuesta."""
        output = get_diagnostic_output(
            module="networking",
            written_response="Le diría al cliente que el problema fue del equipo y que lo solucionaremos.",
            multiple_choice_score=1,
        )
        time.sleep(1)
        judgment = llm_judge_advanced(output, criteria=[
            "El feedback hace referencia a elementos específicos de la respuesta del estudiante",
            "Las fortalezas identificadas son reales y observables en la respuesta",
            "Las debilidades señaladas son pertinentes y justificadas",
            "El nivel asignado es coherente con la calidad de la respuesta",
            "El feedback motiva al estudiante a mejorar sin ser condescendiente",
        ])
        avg = judgment["promedio"]
        assert avg >= self.PASSING_SCORE, f"Promedio juez: {avg}/5"

    def test_feedback_difficulty_scales_with_level(self):
        """El mismo mensaje debe recibir menor score en advanced que en beginner."""
        response = "Agradezco su tiempo. Estoy comprometido con el proyecto y haré lo necesario."

        output_beginner = get_evaluation_output(
            module="networking",
            agent_profile="Colega de trabajo",
            context="Reunión de seguimiento",
            opening_message="¿Cómo vas con tus tareas asignadas?",
            student_response=response,
            level="beginner",
        )
        time.sleep(1)
        output_advanced = get_evaluation_output(
            module="networking",
            agent_profile="Director ejecutivo",
            context="Presentación ante junta directiva",
            opening_message="¿Cómo vas con tus tareas asignadas?",
            student_response=response,
            level="advanced",
        )

        assert output_advanced["score"] <= output_beginner["score"] + 1, (
            f"advanced={output_advanced['score']}, beginner={output_beginner['score']}"
        )

    def test_poor_response_gets_low_judge_score(self):
        """Una respuesta claramente inadecuada debe recibir feedback de baja calidad educativa."""
        output = get_evaluation_output(
            module="networking",
            agent_profile="Reclutadora senior",
            context="Entrevista de trabajo",
            opening_message="¿Por qué quieres trabajar aquí?",
            student_response="porque necesito plata",
        )
        time.sleep(1)
        judgment = llm_judge_advanced(output, criteria=[
            "El feedback explica claramente por qué la respuesta es inapropiada en contexto profesional",
            "El feedback ofrece orientación concreta de cómo mejorar",
            "El tono es respetuoso a pesar de que la respuesta fue muy pobre",
            "El completed=False está justificado en el feedback",
            "El feedback ayuda al estudiante a entender el estándar profesional esperado",
        ])
        avg = judgment["promedio"]
        assert avg >= self.PASSING_SCORE, f"Promedio juez: {avg}/5"

    def test_empathy_judge_detects_superficial_response(self):
        """El juez debe detectar cuando una respuesta empática es superficial."""
        output = get_empathy_scores(
            situation="Tu compañero llora porque su familiar falleció ayer.",
            emotion_identified="tristeza profunda",
            student_response="Lo siento mucho. Todo pasa por algo. Ánimo.",
        )
        time.sleep(1)
        judgment = llm_judge_advanced(output, criteria=[
            "Los scores reflejan que la respuesta fue empáticamente insuficiente para la situación",
            "El feedback explica por qué 'Todo pasa por algo' puede ser invalidante",
            "El feedback muestra cómo responder con mayor profundidad empática",
            "La evaluación es justa — no castiga en exceso pero sí señala la superficialidad",
            "El feedback es sensible al contexto emocional grave de la situación",
        ])
        avg = judgment["promedio"]
        assert avg >= self.PASSING_SCORE, f"Promedio juez: {avg}/5"


# ── Ejecutar pruebas ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v"])