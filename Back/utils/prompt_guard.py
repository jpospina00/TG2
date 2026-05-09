# utils/prompt_guard.py
# Propósito: Validar y sanitizar texto del usuario antes de incluirlo en prompts de IA.
#            Detecta intentos de prompt injection y limpia caracteres peligrosos.
# Uso: llamar sanitize_user_input() sobre cualquier campo de texto libre del usuario
#      antes de interpolarlo en un prompt.
# Fecha: 2026-05-08

import re
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ── Límites de longitud por tipo de campo ────────────────────────────────────
MAX_LENGTHS = {
    "written_response": 2000,   # respuesta en reto simple/diagnóstico
    "message":          1000,   # turno conversacional
    "written":           500,   # texto genérico corto
}

# ── Patrones de prompt injection conocidos ───────────────────────────────────
# Se buscan en lowercase para ser case-insensitive.
_INJECTION_PATTERNS: list[re.Pattern] = [
    # Instrucciones directas al modelo
    re.compile(r"\bignora\b.{0,30}\b(instrucciones?|sistema|anterior)\b", re.I),
    re.compile(r"\bignore\b.{0,30}\b(instructions?|system|previous|above)\b", re.I),
    re.compile(r"\bforget\b.{0,30}\b(instructions?|everything|context)\b", re.I),
    re.compile(r"\bolvida\b.{0,30}\b(instrucciones?|todo|contexto)\b", re.I),

    # Comandos de rol / jailbreak clásicos
    re.compile(r"\bactúa\s+como\b", re.I),
    re.compile(r"\bact\s+as\b.{0,20}\b(admin|root|system|jailbreak|dan)\b", re.I),
    re.compile(r"\byou\s+are\s+now\b", re.I),
    re.compile(r"\bahora\s+eres\b", re.I),
    re.compile(r"\bpretend\s+(you\s+are|to\s+be)\b", re.I),
    re.compile(r"\bfinge\s+(ser|que\s+eres)\b", re.I),

    # Inyección de marcadores de sistema
    re.compile(r"<\|.{0,20}\|>"),                        # <|im_start|> etc.
    re.compile(r"\[INST\]|\[/INST\]|\[SYS\]"),           # Llama tokens
    re.compile(r"###\s*(system|human|assistant|user)\b", re.I),  # Alpaca/Mistral
    re.compile(r"<<SYS>>|<</SYS>>"),

    # Intentos de exfiltración / ejecución
    re.compile(r"\brepite\b.{0,40}\b(sistema|instrucciones?|prompt)\b", re.I),
    re.compile(r"\brepeat\b.{0,40}\b(system|instructions?|prompt)\b", re.I),
    re.compile(r"\bmuestra\b.{0,30}\b(prompt|instrucciones?|sistema)\b", re.I),
    re.compile(r"\bshow\b.{0,30}\b(prompt|instructions?|system)\b", re.I),
    re.compile(r"\bprint\s*\(", re.I),
    re.compile(r"\beval\s*\(", re.I),
    re.compile(r"\bexec\s*\(", re.I),

    # DAN y variantes conocidas
    re.compile(r"\bdan\b.{0,30}\bmode\b", re.I),
    re.compile(r"\bjailbreak\b", re.I),
    re.compile(r"\bdeveloper\s+mode\b", re.I),

    # Salto de contexto con delimitadores
    re.compile(r"---+\s*(system|instruccion|nueva tarea)", re.I),
    re.compile(r"={3,}\s*(system|instruccion)", re.I),
]

# ── Caracteres / secuencias a limpiar (no bloquear, solo remover) ─────────────
_CLEANUP_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Tags HTML/XML que no tienen sentido en texto libre
    (re.compile(r"<[^>]{0,80}>"), ""),
    # Caracteres de control excepto \n y \t
    (re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"), ""),
    # Secuencias de escape de terminal (ANSI)
    (re.compile(r"\x1b\[[0-9;]*m"), ""),
    # Múltiples saltos de línea consecutivos → máximo 2
    (re.compile(r"\n{3,}"), "\n\n"),
]


def sanitize_user_input(
    text: str,
    field_name: str = "written",
    raise_on_injection: bool = True,
) -> str:
    """
    Valida y limpia texto del usuario antes de incluirlo en un prompt de IA.

    Args:
        text:                El texto del usuario a validar.
        field_name:          Clave en MAX_LENGTHS para aplicar el límite correcto.
        raise_on_injection:  Si True lanza HTTPException 400; si False solo loguea y limpia.

    Returns:
        El texto saneado, listo para interpolarse en un prompt.

    Raises:
        HTTPException 400 si se detecta un intento de inyección (cuando raise_on_injection=True).
        HTTPException 422 si el texto excede el límite de longitud.
    """
    if not isinstance(text, str):
        return ""

    # 1. Límite de longitud
    max_len = MAX_LENGTHS.get(field_name, MAX_LENGTHS["written"])
    if len(text) > max_len:
        raise HTTPException(
            status_code=422,
            detail=f"El campo '{field_name}' no puede superar {max_len} caracteres.",
        )

    # 2. Detección de inyección
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(
                "Posible prompt injection detectado | campo=%s | patron=%s | texto=%r",
                field_name, pattern.pattern, text[:200],
            )
            if raise_on_injection:
                raise HTTPException(
                    status_code=400,
                    detail="El texto enviado contiene contenido no permitido.",
                )
            # Si no se lanza, al menos se trunca el match
            text = pattern.sub("[contenido eliminado]", text)

    # 3. Limpieza de caracteres peligrosos
    for pattern, replacement in _CLEANUP_PATTERNS:
        text = pattern.sub(replacement, text)

    return text.strip()


def sanitize_conversation_history(messages: list[dict]) -> list[dict]:
    """
    Sanitiza el historial de mensajes de una conversación.
    Solo limpia los mensajes con role='user'; los del agente no vienen del cliente.
    """
    clean = []
    for msg in messages:
        if msg.get("role") in ("user", "student"):
            clean.append({
                **msg,
                "content": sanitize_user_input(msg.get("content", ""), field_name="message"),
            })
        else:
            clean.append(msg)
    return clean