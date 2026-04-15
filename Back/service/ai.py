# ai.py
# Propósito: Servicio de IA — evaluación, generación de retos y diagnóstico
# Dependencias: groq, chromadb, service/rag
# Fecha: 2026-03-20

from groq import Groq
from config import settings
from service.rag import get_full_context
import json

# ── Prompts del sistema por módulo ────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "empathy": """You are an expert in empathic written communication.
Your role is to evaluate the student's response and provide structured,
constructive feedback in Spanish.

Evaluate based on these criteria:
1. Emotional recognition — Did the student acknowledge the other person's feelings?
2. Empathic language — Did they use validating, warm, non-judgmental language?
3. Clarity — Was the message clear and easy to understand?
4. Context coherence — Was the response appropriate to the situation?

At the end, indicate clearly whether the student PASSED or needs more practice.
Always respond in Spanish. Be specific, encouraging, and constructive.

End your response with exactly one of these lines:
RESULTADO: APROBADO
RESULTADO: NO APROBADO""",

    "networking": """You are an expert in professional written communication and networking.
Your role is to evaluate the student's response and provide structured,
constructive feedback in Spanish.

Evaluate based on these criteria:
1. Communicative objective — Is the purpose of the message clear?
2. Message structure — Is it well organized?
3. Formality level — Is the tone appropriate for a professional context?
4. Context adequacy — Is the response aligned with the professional scenario?

At the end, indicate clearly whether the student PASSED or needs more practice.
Always respond in Spanish. Be specific, encouraging, and constructive.

End your response with exactly one of these lines:
RESULTADO: APROBADO
RESULTADO: NO APROBADO"""
}

AGENT_SYSTEM_PROMPTS = {
    "empathy": """You are playing the role of a virtual agent in a soft skills training system.
Your persona and emotional state are described below.
Respond naturally and authentically to the student, staying in character.
Keep your responses concise (2-4 sentences).
Do NOT break character. Do NOT give feedback or evaluations.
Respond in Spanish.""",

    "networking": """You are playing the role of a professional contact in a networking simulation.
Your professional profile and context are described below.
Respond naturally and realistically as this professional would.
Keep your responses concise (2-4 sentences).
Do NOT break character. Do NOT give feedback or evaluations.
Respond in Spanish."""
}

SPECIALIZATION_LABELS = {
    "ai": "Inteligencia Artificial y Machine Learning",
    "backend": "Desarrollo Backend",
    "frontend": "Desarrollo Frontend",
    "devops": "DevOps e Infraestructura",
    "data": "Ciencia de Datos y Analytics",
    "security": "Ciberseguridad",
    "mobile": "Desarrollo Móvil",
    "other": "Ingeniería de Sistemas general",
}


# ── Fallback entre múltiples API keys ─────────────────────────────────────────

def get_groq_client() -> Groq:
    keys = settings.groq_keys_list
    if not keys:
        raise Exception("No Groq API keys configured")

    for key in keys:
        try:
            client = Groq(api_key=key)
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            return client
        except Exception:
            continue

    raise Exception("All Groq API keys have exceeded their daily quota")


def call_groq(messages: list[dict], max_tokens: int = 1000) -> str:
    client = get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


# ── Flujo de reto SIMPLE ──────────────────────────────────────────────────────

def evaluate_simple_response(
    module_name: str,
    level: str,
    agent_profile: str,
    context: str,
    opening_message: str,
    student_response: str
) -> tuple[str, bool]:
    rag = get_full_context(module_name, level, agent_profile)

    # FIX 1: labels del RAG block en español
    rag_block = ""
    if rag["evaluation_context"]:
        rag_block += f"\n\n--- Referencia de Evaluación ---\n{rag['evaluation_context']}"
    if rag["example_context"]:
        rag_block += f"\n\n--- Ejemplo de Respuesta Excelente ---\n{rag['example_context']}"
    if rag["agent_context"]:
        rag_block += f"\n\n--- Referencia de Comportamiento del Agente ---\n{rag['agent_context']}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[module_name]},
        {
            "role": "user",
            "content": f"""
Contexto del escenario: {context}
Perfil del agente: {agent_profile}
Mensaje inicial del agente: "{opening_message}"
Respuesta del estudiante: "{student_response}"
{rag_block}

Evalúa la respuesta del estudiante basándote en los criterios y el material de referencia.
Termina con RESULTADO: APROBADO o RESULTADO: NO APROBADO.
"""
        }
    ]

    feedback = call_groq(messages)
    completed = "RESULTADO: APROBADO" in feedback
    return feedback, completed


# ── Flujo de reto CONVERSACIONAL ──────────────────────────────────────────────

def generate_agent_reply(
    module_name: str,
    level: str,
    agent_profile: str,
    context: str,
    conversation_history: list[dict]
) -> str:
    rag = get_full_context(module_name, level, agent_profile)

    # FIX 1: label en español
    agent_context_block = ""
    if rag["agent_context"]:
        agent_context_block = f"\n\n--- Referencia de Comportamiento ---\n{rag['agent_context']}"

    system_content = f"""{AGENT_SYSTEM_PROMPTS[module_name]}

Perfil del agente: {agent_profile}
Contexto: {context}{agent_context_block}"""

    groq_messages = [{"role": "system", "content": system_content}]
    for msg in conversation_history:
        role = "assistant" if msg["role"] == "agent" else "user"
        groq_messages.append({"role": role, "content": msg["content"]})

    return call_groq(groq_messages, max_tokens=300)


def evaluate_conversation(
    module_name: str,
    level: str,
    agent_profile: str,
    context: str,
    conversation_history: list[dict]
) -> tuple[str, bool]:
    rag = get_full_context(module_name, level, agent_profile)

    # FIX 1: labels en español
    rag_block = ""
    if rag["evaluation_context"]:
        rag_block += f"\n\n--- Referencia de Evaluación ---\n{rag['evaluation_context']}"
    if rag["example_context"]:
        rag_block += f"\n\n--- Ejemplo de Respuesta Excelente ---\n{rag['example_context']}"

    history_text = ""
    for msg in conversation_history:
        label = "Agente" if msg["role"] == "agent" else "Estudiante"
        history_text += f"{label}: {msg['content']}\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[module_name]},
        {
            "role": "user",
            "content": f"""
Contexto del escenario: {context}
Perfil del agente: {agent_profile}

Conversación completa:
{history_text}
{rag_block}

Evalúa el desempeño general del estudiante.
Termina con RESULTADO: APROBADO o RESULTADO: NO APROBADO.
"""
        }
    ]

    feedback = call_groq(messages)
    completed = "RESULTADO: APROBADO" in feedback
    return feedback, completed


# ── Generación dinámica de retos ──────────────────────────────────────────────

def generate_new_challenge(
    module_name: str,
    level: str,
    challenge_type: str
) -> dict:
    rag = get_full_context(module_name, level, "generación de nuevo reto")

    # FIX 3: aprovechar challenge_pattern y personalization_guide
    rag_block = ""
    if rag["evaluation_context"]:
        rag_block += f"\n\nReferencia para este nivel:\n{rag['evaluation_context']}"
    if rag["challenge_pattern"]:
        rag_block += f"\n\nPatrón de reto para este nivel:\n{rag['challenge_pattern']}"
    if rag["personalization_guide"]:
        rag_block += f"\n\nGuía de personalización:\n{rag['personalization_guide']}"

    messages = [
        {
            "role": "system",
            "content": "Eres un diseñador de currículum para un sistema de entrenamiento en habilidades blandas. Genera retos realistas. Responde siempre con JSON válido únicamente, sin texto adicional."
        },
        {
            "role": "user",
            "content": f"""
Genera un nuevo reto de {module_name}:
- Nivel: {level}
- Tipo: {challenge_type}
{rag_block}

Devuelve ÚNICAMENTE un objeto JSON:
{{
  "agent_profile": "Descripción breve del agente virtual en español",
  "context": "Contexto de la situación comunicativa en español",
  "opening_message": "Primer mensaje del agente en español"
}}
"""
        }
    ]

    raw = call_groq(messages, max_tokens=500)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


# ── Diagnóstico inicial ───────────────────────────────────────────────────────

async def generate_diagnostic_questions(module_name: str) -> dict:
    """Genera 3 preguntas de opción múltiple para el diagnóstico."""
    client = get_groq_client()

    # FIX 2: argumentos corregidos — level e agent_profile en el orden correcto
    ctx = get_full_context(module_name, "beginner", "preguntas de diagnóstico")
    context = ctx.get("evaluation_context", "")

    if module_name == "empathy":
        prompt = f"""Eres un experto en comunicación empática. 
Genera exactamente 3 preguntas de opción múltiple en español para evaluar el nivel de empatía cognitiva de un estudiante universitario de Ingeniería de Sistemas.

Contexto de referencia:
{context}

Reglas estrictas:
- Cada pregunta debe presentar una situación comunicativa emocional real
- Cada pregunta tiene exactamente 4 opciones (A, B, C, D)
- Solo una opción es correcta
- Las opciones incorrectas deben ser plausibles pero claramente menos empáticas
- Nivel de dificultad: mixto (1 fácil, 1 medio, 1 difícil)
- Las 3 preguntas DEBEN cubrir contextos completamente diferentes:
  * Pregunta 1: conflicto grupal o de equipo
  * Pregunta 2: situación de estrés o agotamiento personal
  * Pregunta 3: error, culpa o decepción
- NUNCA repitas el mismo contexto en dos preguntas del mismo diagnóstico

Responde ÚNICAMENTE en este formato JSON sin texto adicional:
{{
  "questions": [
    {{
      "id": 1,
      "situation": "descripción de la situación",
      "question": "¿Cuál sería la respuesta más empática?",
      "options": {{
        "A": "opción A",
        "B": "opción B", 
        "C": "opción C",
        "D": "opción D"
      }},
      "correct": "A",
      "explanation": "explicación breve de por qué esta es la mejor respuesta"
    }}
  ]
}}"""
    else:
        prompt = f"""Eres un experto en networking profesional.
Genera exactamente 3 preguntas de opción múltiple en español para evaluar el nivel de networking de un estudiante universitario de Ingeniería de Sistemas.

Contexto de referencia:
{context}

Reglas estrictas:
- Cada pregunta debe presentar una situación de networking profesional real
- Cada pregunta tiene exactamente 4 opciones (A, B, C, D)
- Solo una opción es correcta
- Las opciones incorrectas deben ser plausibles pero menos efectivas profesionalmente
- Nivel de dificultad: mixto (1 fácil, 1 medio, 1 difícil)
- Las 3 preguntas DEBEN cubrir contextos completamente diferentes:
  * Pregunta 1: contexto presencial (feria, evento, conferencia)
  * Pregunta 2: contexto digital (LinkedIn, correo, mensaje de seguimiento)
  * Pregunta 3: contexto académico-profesional (profesor, mentor, profesional del área)
- NUNCA repitas el mismo contexto en dos preguntas del mismo diagnóstico

Responde ÚNICAMENTE en este formato JSON sin texto adicional:
{{
  "questions": [
    {{
      "id": 1,
      "situation": "descripción de la situación",
      "question": "¿Cuál sería el mensaje más efectivo?",
      "options": {{
        "A": "opción A",
        "B": "opción B",
        "C": "opción C", 
        "D": "opción D"
      }},
      "correct": "B",
      "explanation": "explicación breve de por qué esta es la mejor respuesta"
    }}
  ]
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.7,
    )

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)


async def generate_diagnostic_scenario(module_name: str) -> dict:
    """Genera el escenario de escritura para el diagnóstico."""
    client = get_groq_client()

    if module_name == "empathy":
        prompt = """Genera un escenario de comunicación empática de dificultad media para evaluar a un estudiante de Ingeniería de Sistemas.
El escenario debe estar ambientado en un contexto de desarrollo de software, trabajo en equipo técnico o vida universitaria en sistemas.

Responde ÚNICAMENTE en este formato JSON sin texto adicional:
{
  "agent_profile": "descripción breve del personaje",
  "context": "contexto de la situación en 1-2 oraciones",
  "opening_message": "mensaje del agente virtual al estudiante (máximo 3 oraciones)"
}

El mensaje debe requerir una respuesta empática pero no ser extremadamente difícil."""
    else:
        prompt = """Genera un escenario de networking profesional de dificultad media para evaluar a un estudiante de Ingeniería de Sistemas.
El escenario debe estar ambientado en el sector tecnológico: empresas de software, startups, conferencias tech, LinkedIn profesional del área.

Responde ÚNICAMENTE en este formato JSON sin texto adicional:
{
  "agent_profile": "descripción breve del personaje profesional del sector tech",
  "context": "contexto de la situación en 1-2 oraciones",
  "opening_message": "mensaje del agente virtual al estudiante (máximo 3 oraciones)"
}

El mensaje debe requerir una respuesta de networking clara y profesional pero no extremadamente difícil."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.8,
    )

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)


async def evaluate_diagnostic_response(
    module_name: str,
    multiple_choice_score: int,
    scenario: dict,
    written_response: str,
) -> dict:
    """Evalúa la respuesta escrita del diagnóstico y determina el nivel."""
    client = get_groq_client()

    # FIX 2: argumentos corregidos — level="intermediate", agent_profile descriptivo
    ctx = get_full_context(module_name, "intermediate", "evaluación de diagnóstico")
    context = ctx.get("evaluation_context", "")

    if module_name == "empathy":
        criteria = "reconocimiento emocional, lenguaje empático, claridad y coherencia contextual"
    else:
        criteria = "claridad del objetivo, estructura del mensaje, formalidad y adecuación al contexto"

    prompt = f"""Eres un experto evaluador de habilidades blandas.

Evalúa el desempeño diagnóstico de un estudiante universitario de Ingeniería de Sistemas en el módulo de {module_name}.

DATOS DEL DIAGNÓSTICO:
- Puntaje en preguntas de opción múltiple: {multiple_choice_score}/3
- Escenario de escritura:
  - Perfil del agente: {scenario['agent_profile']}
  - Contexto: {scenario['context']}
  - Mensaje del agente: {scenario['opening_message']}
- Respuesta escrita del estudiante: {written_response}

CRITERIOS DE EVALUACIÓN:
{context}
Criterios específicos a evaluar: {criteria}

INSTRUCCIONES:
1. Analiza la respuesta escrita considerando los criterios
2. Combina el puntaje de opción múltiple ({multiple_choice_score}/3) con la calidad de la respuesta escrita
3. Determina el nivel de entrada más apropiado
4. Identifica fortalezas y debilidades específicas

Lógica de nivel — la respuesta escrita tiene MÁS peso que el puntaje múltiple:
- advanced: puntaje alto (3) Y respuesta escrita de alta calidad
- intermediate: puntaje medio (2) Y respuesta aceptable
              O puntaje bajo (0-1) PERO respuesta escrita de alta calidad
- beginner: puntaje bajo (0-1) Y respuesta escrita con deficiencias básicas

IMPORTANTE: Si la respuesta escrita es de alta calidad, nunca asignes beginner
independientemente del puntaje de opción múltiple.

REGLA IMPORTANTE: Nunca reproduzcas ni cites la respuesta del estudiante en ningún campo del JSON.

Responde ÚNICAMENTE en este formato JSON sin texto adicional:
{{
  "level_result": "beginner|intermediate|advanced",
  "written_feedback": "retroalimentación constructiva en 2-3 oraciones. NO copies ni reproduzcas la respuesta del estudiante. Analiza su calidad sin citarla.",
  "strengths": "fortalezas detectadas en 1-2 oraciones",
  "weaknesses": "áreas de mejora detectadas en 1-2 oraciones",
  "justification": "justificación breve del nivel asignado"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.3,
    )

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)


async def generate_personalized_challenges(
    module_name: str,
    level: str,
    user_id: int,
    diagnostic: dict,
    count: int = 5,
    student_profile: dict = None,
) -> list[dict]:
    """Genera retos personalizados basados en el diagnóstico y perfil del usuario."""
    client = get_groq_client()

    ctx = get_full_context(module_name, level, "generación de retos personalizados")
    pattern_context = ctx.get("challenge_pattern", "")
    personalization_context = ctx.get("personalization_guide", "")

    if module_name == "empathy":
        level_specs = {
            "beginner": """
ESPECIFICACIONES NIVEL INICIAL — EMPATÍA:
- La emoción del agente debe ser EXPLÍCITA y clara (usa frases como 'me siento frustrado', 'estoy agobiado', 'me duele')
- Situaciones simples con UN solo problema emocional identificable
- Tipo: 4 retos simple, 1 conversacional
- El agente NO hace preguntas complejas ni tiene actitud defensiva""",

            "intermediate": """
ESPECIFICACIONES NIVEL INTERMEDIO — EMPATÍA:
- La emoción del agente es IMPLÍCITA — el estudiante debe inferirla del contexto
- Incluye tensión interpersonal leve: malentendidos, decisiones que afectaron al otro
- Tipo: 2 retos simple, 3 conversacionales
- El agente puede hacer preguntas o expresar expectativas no cumplidas""",

            "advanced": """
ESPECIFICACIONES NIVEL AVANZADO — EMPATÍA:
- La emoción es AMBIGUA o CONTRADICTORIA — puede interpretarse de varias formas
- Situaciones complejas: burnout, errores graves, crisis personal
- Tipo: 1 reto simple, 4 conversacionales
- El agente puede ponerse defensivo o resistirse al apoyo"""
        }
    else:
        level_specs = {
            "beginner": """
ESPECIFICACIONES NIVEL INICIAL — NETWORKING:
- El agente es RECEPTIVO, amigable y abierto a la conversación
- Tipo: 4 retos simple, 1 conversacional
- El agente NO cuestiona ni presiona — facilita la conversación""",

            "intermediate": """
ESPECIFICACIONES NIVEL INTERMEDIO — NETWORKING:
- El agente es PROFESIONAL y hace preguntas que requieren respuestas específicas
- Tipo: 2 retos simple, 3 conversacionales
- El agente espera especificidad — respuestas vagas no son suficientes""",

            "advanced": """
ESPECIFICACIONES NIVEL AVANZADO — NETWORKING:
- El agente es ESCÉPTICO, directo y cuestiona activamente la credibilidad del estudiante
- Tipo: 1 reto simple, 4 conversacionales
- El agente NO facilita — el estudiante debe ganarse la conversación"""
        }

    level_spec = level_specs.get(level, "")

    # Bloque de perfil del estudiante
    profile_block = ""
    if student_profile and student_profile.get("has_profile"):
        spec = SPECIALIZATION_LABELS.get(
            student_profile.get("specialization", ""), "Ingeniería de Sistemas general"
        )
        profile_block = f"""
PERFIL ACADÉMICO DEL ESTUDIANTE:
- Semestre: {student_profile.get('semester')}
- Área de especialización: {spec}
- Auto-percepción de nivel en habilidades blandas: {student_profile.get('self_assessed_level')}

INSTRUCCIÓN CRÍTICA DE CONTEXTUALIZACIÓN:
Todos los escenarios deben estar ambientados en contextos reales de {spec} dentro de la Ingeniería de Sistemas.
- Para empatía: usa situaciones de equipos de desarrollo, proyectos de software, revisiones de código, bugs en producción, sprints, hackathons, trabajo remoto.
- Para networking: usa situaciones con reclutadores tech, ingenieros senior, CTOs, data scientists, conferencias como PyCon, Google I/O o meetups de tecnología, LinkedIn profesional del área tech.
- Los personajes deben tener roles reales del área: desarrollador senior, tech lead, data scientist, DevOps engineer, product manager, CTO de startup, reclutador tech, etc.
- NO uses contextos genéricos universitarios — usa contextos específicos y reales de {spec}.
"""

    prompt = f"""IMPORTANTE: Toda tu respuesta debe estar en español. 
Ningún campo puede contener palabras en inglés.

Eres un experto en diseño de retos educativos para habilidades blandas en estudiantes de Ingeniería de Sistemas.

Genera exactamente {count} retos personalizados en español para el módulo de {module_name}, nivel {level}.

PERFIL DEL ESTUDIANTE (basado en diagnóstico):
- Nivel asignado: {level}
- Fortalezas: {diagnostic.get('strengths', 'No especificadas')}
- Debilidades: {diagnostic.get('weaknesses', 'No especificadas')}
- Feedback del diagnóstico: {diagnostic.get('written_feedback', 'No disponible')}
{profile_block}
{level_spec}

PATRONES DE RETOS PARA ESTE NIVEL:
{pattern_context}

GUÍA DE PERSONALIZACIÓN:
{personalization_context}

REGLAS IMPORTANTES:
1. Los {count} retos deben cubrir situaciones COMPLETAMENTE diferentes entre sí
2. NO repitas el mismo tipo de agente o contexto en dos retos del mismo nivel
3. Personaliza según las debilidades detectadas en el diagnóstico
4. Todo en español: agent_profile, context, opening_message
5. Sigue estrictamente las especificaciones de tipo (simple/conversational) del nivel
6. El opening_message debe reflejar el nivel de complejidad emocional o profesional especificado
7. OBLIGATORIO: Todo 100% en español. Ninguna palabra en inglés.

Responde ÚNICAMENTE en este formato JSON sin texto adicional:
{{
  "challenges": [
    {{
      "agent_profile": "descripción del perfil del agente virtual",
      "context": "contexto de la situación comunicativa",
      "opening_message": "primer mensaje que lanza el agente al estudiante",
      "type": "simple|conversational"
    }}
  ]
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
        temperature=0.8,
    )

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()
    result = json.loads(content)
    return result["challenges"]