// Guide.js
// Propósito: Guía de aprendizaje por módulo con conceptos, tips y ejemplos
// Dependencias: react, react-router-dom, react-icons
// Fecha: 2026-03-20

import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { FiArrowLeft, FiChevronDown, FiChevronUp } from "react-icons/fi";
import "./Guide.css";

const GUIDES = {
  empathy: {
    title: "Comunicación Empática",
    color: "#2563EB",
    intro: "La comunicación empática es la capacidad de reconocer, comprender y validar las emociones de otra persona antes de responder. No se trata de estar de acuerdo con todo, sino de hacer sentir al otro que fue escuchado.",
    sections: [
      {
        title: "¿Qué es la empatía cognitiva?",
        content: "La empatía cognitiva es la capacidad de identificar y comprender el estado emocional de otra persona desde su perspectiva, sin necesariamente compartir esa emoción. Es diferente a la empatía afectiva, que implica sentir lo mismo que el otro. En la comunicación escrita, entrenamos la empatía cognitiva: leer el mensaje, identificar la emoción detrás de las palabras y formular una respuesta alineada con ese estado emocional.",
      },
      {
        title: "Los 4 criterios de evaluación",
        content: null,
        list: [
          {
            name: "Reconocimiento emocional",
            desc: "¿Nombras o validas la emoción que expresa el otro? Una respuesta empática siempre empieza por reconocer cómo se siente la otra persona, no por ofrecer soluciones.",
          },
          {
            name: "Lenguaje empático",
            desc: "¿Usas un tono cálido, no juicioso y validante? Evita frases como 'no deberías sentirte así' o 'eso no es para tanto'. Prefiere frases como 'entiendo que eso es difícil' o 'tiene sentido que te sientas así'.",
          },
          {
            name: "Claridad",
            desc: "¿Tu mensaje es fácil de entender? Una respuesta empática no necesita ser larga, pero sí clara y directa. Evita rodeos innecesarios.",
          },
          {
            name: "Coherencia contextual",
            desc: "¿Tu respuesta es apropiada para la situación específica planteada? No respondas de forma genérica. Muestra que leíste y entendiste el contexto particular.",
          },
        ],
      },
      {
        title: "Errores comunes",
        content: null,
        list: [
          { name: "Minimizar la emoción", desc: "'No es para tanto' o 'otros tienen problemas peores' invalidan lo que siente el otro." },
          { name: "Saltar a soluciones", desc: "Ofrecer soluciones antes de validar la emoción hace sentir al otro que no fue escuchado." },
          { name: "Hacer juicios", desc: "Frases como 'deberías haber hecho X' generan defensividad en lugar de conexión." },
          { name: "Responder de forma genérica", desc: "Una respuesta que podría aplicar a cualquier situación no demuestra que entendiste el contexto específico." },
        ],
      },
      {
        title: "La técnica del sándwich empático",
        content: "Una estructura útil para respuestas empáticas es: (1) Reconoce la emoción, (2) Valida el contexto, (3) Ofrece apoyo o abre el diálogo. Esta estructura asegura que primero conectas emocionalmente antes de pasar a lo práctico.",
      },
      {
        title: "Ejemplo de respuesta excelente",
        content: null,
        example: {
          scenario: "Mensaje del agente: 'No entiendo por qué nadie escucha mis ideas. Siempre pongo el esfuerzo y siento que soy invisible en este grupo.'",
          bad: "Respuesta NO empática: 'Tienes que hablar más fuerte en las reuniones y ser más asertivo. Si nadie te escucha quizás es porque no te expresas bien.'",
          good: "Respuesta empática: 'Entiendo que eso es muy frustrante, especialmente cuando sientes que estás poniendo todo el esfuerzo. Nadie debería sentirse invisible en su propio equipo. ¿Qué idea específicamente sientes que no fue considerada? Me gustaría escucharte.'",
          why: "¿Por qué funciona? Primero valida la emoción (frustración), luego reconoce el esfuerzo, y finalmente abre el diálogo con una pregunta concreta. No ofrece consejos no solicitados ni hace juicios.",
        },
      },
      {
        title: "Tips para los retos",
        content: null,
        list: [
          { name: "Lee despacio", desc: "Antes de escribir, identifica qué emoción específica está expresando el agente. ¿Frustración? ¿Tristeza? ¿Vergüenza? ¿Agotamiento?" },
          { name: "Nombra la emoción", desc: "Usa frases como 'entiendo que te sientes...', 'tiene sentido que...', 'imagino que eso debe ser...'." },
          { name: "No te apresures a resolver", desc: "En los niveles iniciales, validar la emoción es suficiente. No necesitas resolver el problema del agente." },
          { name: "Sé específico", desc: "Menciona algo concreto del mensaje del agente para mostrar que realmente leíste y entendiste su situación." },
        ],
      },
    ],
  },
  networking: {
    title: "Networking Profesional",
    color: "#0EA5E9",
    intro: "El networking profesional es la construcción estratégica de relaciones significativas en contextos académicos y laborales. No se trata de coleccionar contactos, sino de establecer conexiones genuinas que generen valor mutuo a través de una comunicación escrita clara, formal y orientada a un objetivo.",
    sections: [
      {
        title: "¿Qué es el networking efectivo?",
        content: "El networking efectivo implica comunicarse con claridad sobre quién eres, qué buscas y por qué contactas a esa persona específica. Un mensaje de networking exitoso no es genérico: demuestra que investigaste a la persona y que tienes una razón concreta para contactarla. La autoeficacia, es decir la confianza en tu capacidad para iniciar estas interacciones, se desarrolla con práctica.",
      },
      {
        title: "Los 4 criterios de evaluación",
        content: null,
        list: [
          {
            name: "Objetivo comunicativo",
            desc: "¿Queda claro desde el inicio qué buscas con este mensaje? El receptor debe entender en las primeras líneas qué quieres y por qué le escribes a él específicamente.",
          },
          {
            name: "Estructura del mensaje",
            desc: "¿El mensaje tiene una apertura, un cuerpo y un cierre claros? Una buena estructura incluye: contexto de quién eres, razón específica del contacto, y una solicitud concreta y razonable.",
          },
          {
            name: "Nivel de formalidad",
            desc: "¿El tono es apropiado para el contexto profesional? Ni demasiado informal (como si fuera un amigo) ni demasiado rígido. Adapta el tono según si es un profesor, reclutador, profesional del área o compañero.",
          },
          {
            name: "Adecuación al contexto",
            desc: "¿La respuesta es apropiada para la situación específica planteada? Un mensaje a un reclutador en una feria es diferente a uno para pedir mentoría a un profesional senior.",
          },
        ],
      },
      {
        title: "Errores comunes",
        content: null,
        list: [
          { name: "Mensajes genéricos", desc: "'Hola, me interesa conectar contigo' no dice nada. Siempre personaliza con una razón específica." },
          { name: "Solicitudes vagas", desc: "'Quisiera hablar contigo sobre mi carrera' es demasiado vago. Sé específico: '¿Podría tener 20 minutos de tu tiempo para una charla informativa?'" },
          { name: "Tono inapropiado", desc: "Ser demasiado informal con un profesional senior o demasiado rígido con un compañero de evento genera distancia." },
          { name: "No investigar al contacto", desc: "Si escribes sin mencionar algo específico sobre la persona o su trabajo, el mensaje pierde credibilidad y parece masivo." },
          { name: "No hacer una solicitud clara", desc: "Terminar el mensaje con 'avísame si quieres hablar' es pasivo. Haz una solicitud concreta y razonable." },
        ],
      },
      {
        title: "Estructura recomendada de un mensaje de networking",
        content: null,
        list: [
          { name: "Apertura contextual", desc: "¿Quién eres y por qué contactas a esta persona en particular? Ejemplo: 'Soy estudiante de último semestre de Ingeniería de Sistemas y encontré tu trabajo sobre arquitecturas distribuidas muy relevante para mi proyecto de grado.'" },
          { name: "Propuesta de valor o razón de contacto", desc: "¿Qué tienes para ofrecer o qué busca específicamente de esa persona? No pidas trabajo directamente en el primer mensaje." },
          { name: "Solicitud concreta y razonable", desc: "¿Qué pides específicamente? Una llamada de 20 minutos, una respuesta a una pregunta puntual, o una recomendación de recursos. Cuanto más específico, más fácil es decir sí." },
          { name: "Cierre profesional", desc: "Agradece el tiempo, muestra flexibilidad y deja la puerta abierta. Ejemplo: 'Entiendo que tienes una agenda muy ocupada, cualquier momento que tengas disponible me parece bien.'" },
        ],
      },
      {
        title: "Ejemplo de respuesta excelente",
        content: null,
        example: {
          scenario: "Contexto: Un profesional de software en una empresa que admiras te pregunta: 'Dime brevemente por qué quieres hablar conmigo y qué esperas de esta conversación.'",
          bad: "Respuesta NO efectiva: 'Me interesa mucho tu empresa y quería conocer más sobre lo que hacen. También me gustaría saber cómo conseguiste tu trabajo para poder hacer lo mismo.'",
          good: "Respuesta efectiva: 'Claro, seré breve. Soy estudiante de último semestre de Ingeniería de Sistemas y estoy desarrollando mi proyecto de grado en arquitecturas de microservicios. Leí el artículo que publicaste sobre tolerancia a fallos y me generó preguntas que no he podido resolver leyendo. No busco trabajo en este momento — simplemente valoraría 20 minutos de tu experiencia para entender qué decisiones técnicas priorizarías al inicio de una carrera en backend. ¿Tendrías disponibilidad algún día de esta semana?'",
          why: "¿Por qué funciona? Es específico (menciona el artículo), honesto sobre lo que busca (no un trabajo), hace una solicitud concreta (20 minutos), y muestra preparación y respeto por el tiempo del profesional.",
        },
      },
      {
        title: "Tips para los retos",
        content: null,
        list: [
          { name: "Investiga al agente", desc: "Lee bien el perfil del agente antes de responder. ¿Es un reclutador, un profesor, un profesional senior? Adapta el tono y el contenido." },
          { name: "Sé específico desde el inicio", desc: "Tu primera línea debe dejar claro quién eres y por qué escribes. No des rodeos." },
          { name: "Haz una solicitud concreta", desc: "No termines el mensaje sin una solicitud clara. '¿Podría X?' es mejor que 'avísame si te parece'." },
          { name: "Respeta el tiempo del otro", desc: "Mantén el mensaje conciso. En networking, la brevedad bien estructurada es más efectiva que mensajes largos." },
        ],
      },
    ],
  },
};

function Guide() {
  const { moduleId } = useParams();
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(null);

  const moduleName = moduleId === "1" ? "empathy" : "networking";
  const guide = GUIDES[moduleName];

  if (!guide) {
    return (
      <div className="guide-loading">
        <p>Guía no encontrada.</p>
      </div>
    );
  }

  return (
    <div className="guide-wrap">
      <nav className="guide-navbar">
        <button className="guide-back-btn" onClick={() =>  moduleId === "1" ? navigate(`/empathy/${moduleId}`) : navigate(`/module/${moduleId}`)}>
          <FiArrowLeft size={16} />
          Volver al módulo
        </button>
        <span className="guide-navbar-title">Guía de aprendizaje</span>
        <div style={{ width: 80 }} />
      </nav>

      <div className="guide-content">
        {/* Header */}
        <div className="guide-header" style={{ borderColor: guide.color + "40" }}>
          <div className="guide-header-badge" style={{ background: guide.color + "20", color: guide.color }}>
            Guía
          </div>
          <h1 className="guide-title">{guide.title}</h1>
          <p className="guide-intro">{guide.intro}</p>
        </div>

        {/* Secciones */}
        <div className="guide-sections">
          {guide.sections.map((section, i) => (
            <div key={i} className="guide-section">
              <button
                className="guide-section-header"
                onClick={() => setExpanded(expanded === i ? null : i)}
              >
                <span className="guide-section-title">{section.title}</span>
                {expanded === i
                  ? <FiChevronUp size={18} color="rgba(241,245,249,0.5)" />
                  : <FiChevronDown size={18} color="rgba(241,245,249,0.5)" />
                }
              </button>

              {expanded === i && (
                <div className="guide-section-body">
                  {/* Texto simple */}
                  {section.content && (
                    <p className="guide-text">{section.content}</p>
                  )}

                  {/* Lista de items */}
                  {section.list && (
                    <div className="guide-list">
                      {section.list.map((item, j) => (
                        <div key={j} className="guide-list-item">
                          <div
                            className="guide-list-dot"
                            style={{ background: guide.color }}
                          />
                          <div>
                            <p className="guide-list-name">{item.name}</p>
                            <p className="guide-list-desc">{item.desc}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Ejemplo */}
                  {section.example && (
                    <div className="guide-example">
                      <div className="guide-example-scenario">
                        <p className="guide-example-label">Escenario</p>
                        <p className="guide-example-text">{section.example.scenario}</p>
                      </div>
                      <div className="guide-example-bad">
                        <p className="guide-example-label" style={{ color: "#FCA5A5" }}>
                          ✗ Respuesta no efectiva
                        </p>
                        <p className="guide-example-text">{section.example.bad}</p>
                      </div>
                      <div className="guide-example-good">
                        <p className="guide-example-label" style={{ color: "#6EE7B7" }}>
                          ✓ Respuesta efectiva
                        </p>
                        <p className="guide-example-text">{section.example.good}</p>
                      </div>
                      <div className="guide-example-why">
                        <p className="guide-example-label" style={{ color: "#93C5FD" }}>
                          ¿Por qué funciona?
                        </p>
                        <p className="guide-example-text">{section.example.why}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Botón volver */}
        <button
          className="guide-btn-back"
          onClick={() => moduleId === "1" ? navigate(`/empathy/${moduleId}`) : navigate(`/module/${moduleId}`)}
        >
          Volver al módulo y practicar
        </button>
      </div>
    </div>
  );
}

export default Guide;