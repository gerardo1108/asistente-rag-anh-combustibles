"""Retrieval + generación con LLM, con fallback entre proveedores y con
reformulación de la pregunta como fallback de retrieval.

Antes de tocar el corpus, `responder()` corta con un patrón (`_PATRON_SALUDO`)
para saludos y preguntas sobre la identidad del asistente ("hola", "quién
sos", "qué haces") — nunca van a encontrar nada en el corpus normativo, y
este atajo evita tanto la abstención como una llamada innecesaria a un LLM.

Sigue el patrón validado en `RAG_Gemini_ANH.ipynb`: recupera los chunks más
relevantes del índice Chroma, arma un contexto con trazabilidad a la fuente,
y genera la respuesta restringida a ese contexto. Si ningún chunk supera el
umbral de similitud con la pregunta tal cual, se intenta UNA reformulación
vía LLM (typos, muletillas, contexto de la conversación previa) y se
reintenta la búsqueda una sola vez; si sigue sin resultados, recién ahí se
abstiene. Esto significa que la garantía de "abstención sin llamar a ningún
LLM" (documentada en CLAUDE.md) vale en el camino feliz (primera búsqueda con
resultados), pero no cuando ese camino falla: ahí se paga una llamada extra a
un proveedor de LLM antes de decidir si abstenerse. No se reintenta más de
una vez para no multiplicar esa latencia en preguntas genuinamente fuera del
corpus.

La generación intenta los proveedores en `LLM_PROVEEDORES` en orden (ver
`configuracion.py`); cada uno agota sus propios reintentos ante errores
transitorios antes de pasar al siguiente. Ambos devuelven texto plano con el
mismo `INSTRUCCIONES_SISTEMA`, así que el resto del pipeline no necesita
saber cuál respondió.
"""

import json
import logging
import re
import time
from dataclasses import dataclass

import groq as groq_sdk
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from . import configuracion
from .modelos import ConsultaRagResponse, Fuente

# Texto fijo; se interpola en INSTRUCCIONES_SISTEMA (regla 2) para que el
# LLM y el camino de abstención por retrieval (sin llamar a ningún LLM,
# `responder()`) usen exactamente el mismo texto, sin duplicarlo a mano en
# dos lugares que podrían divergir. No dice "documentos proporcionados": el
# ciudadano no aporta ningún documento a esta conversación, es el asistente
# el que consulta su propio corpus normativo.
MENSAJE_ABSTENCION = (
    "No encontré esa información en la normativa disponible. "
    "Intenta reformular tu pregunta con otras palabras."
)

# Nota de descargo, adjunta en un campo aparte de la respuesta (`nota`, ver
# modelos.py) en vez de pedirle al LLM que la redacte dentro del texto: como
# instrucción en prosa libre ("aclara que..."), el modelo la formulaba y
# formateaba distinto en cada respuesta (con/sin la palabra "Nota", en
# blockquote, a veces con una frase extra pegada) — texto fijo, siempre
# igual, es más simple y confiable que otra regla de prompt.
NOTA_ORIENTATIVA = "Esta respuesta es orientativa y no sustituye la interpretación oficial de la ANH."

# Advertencia para el caso en que la reformulación de pregunta (fallback de
# retrieval, ver `_reformular_pregunta`) falla porque todos los proveedores
# de LLM_PROVEEDORES agotaron sus reintentos — una falla transitoria de
# infraestructura, no una señal de que la pregunta esté genuinamente fuera
# del corpus. Sin esto, ese caso es indistinguible de una abstención normal
# para quien lo lee, y encima el mensaje de abstención sugiere "reformula tu
# pregunta", un consejo equivocado cuando la causa real no tiene nada que
# ver con cómo está redactada.
ADVERTENCIA_LLM_NO_RESPONDIO = "Los proveedores LLM no respondieron. Intenta de nuevo en un momento."

INSTRUCCIONES_SISTEMA = f"""
Eres un asistente que orienta sobre trámites de la ANH usando exclusivamente el CONTEXTO proporcionado.

REGLAS:
1. Utiliza únicamente la información del CONTEXTO.
2. Si la respuesta no está en el contexto, responde exactamente:
   "{MENSAJE_ABSTENCION}"
3. No inventes datos, ejemplos ni aclaraciones que no estén literalmente en
   el CONTEXTO, aunque te parezcan plausibles o razonables (ej.: si el
   CONTEXTO dice "fotografías que solicite el formulario" sin especificar
   cuáles, no inventes qué fotos serían). Si un campo del CONTEXTO es vago
   o no da ejemplos, preséntalo tal cual, sin completarlo por tu cuenta ni
   interpretar la normativa más allá del texto entregado.
4. No menciones la norma, el artículo, ni frases del tipo "(Fuente: ...)" dentro
   de la respuesta: la atribución de fuente se muestra aparte, no hace falta
   repetirla en el texto. Responde el contenido de forma natural.
5. Responde en español, de forma clara y concisa.
6. Si tu respuesta describe el proceso de registro en Ciudadanía Digital
   (AGETIC) —pre-registro, verificación de identidad, tipos de registro—,
   aclara que es un trámite distinto del Formulario Electrónico de registro
   de consumo de combustibles ante la ANH. Si tu respuesta no describe ese
   proceso, no menciones esta distinción, aunque el CONTEXTO incluya
   información sobre Ciudadanía Digital. Esta aclaración es sobre a qué
   trámite pertenece la información, no una licencia para afirmar qué exige
   o no exige el otro trámite: eso solo si está en el CONTEXTO (regla 1).
7. No describas de dónde viene tu información (nada de "según los documentos
   que compartiste/proporcionaste", "basándome en el contexto", ni frases
   similares): el ciudadano no comparte ningún documento en esta
   conversación, y esas frases son confusas. Responde el contenido
   directamente, sin comentar su origen.
"""

# Saludos y preguntas sobre la identidad del asistente ("hola", "quién sos",
# "qué haces") nunca van a encontrar nada en el corpus normativo -es texto
# legal, no autodescriptivo- y terminarían en abstención sin este atajo. Se
# resuelve con un patrón, no con el LLM, para no pagar una llamada y para no
# arriesgar que el modelo invente algo: si el patrón no matchea una variante
# creativa, cae al camino normal y se abstiene igual que hoy, nunca peor.
#
# Todo el mensaje tiene que reducirse a saludo y/o identidad -no alcanza con
# que EMPIECE así-: "Hola, necesito comprar gasolina en un bidón" no debe
# disparar esto solo porque arranca con "Hola" (bug real, encontrado en
# pruebas). Por eso el patrón exige `$` al final en ambas ramas: una sola
# palabra de saludo, opcionalmente seguida de una pregunta de identidad
# ("Hola, ¿quién eres?"), pero nada más después.
_SALUDO = r"(?:hola+|buen[oa]s?\s+(?:d[ií]as?|tardes?|noches?)|buenas)"
_IDENTIDAD = (
    r"(?:qui[ée]n\s+(?:eres|sos|es\s+usted)"
    r"|qu[ée]\s+(?:eres|haces|puedes\s+hacer|sabes\s+hacer)"
    r"|para\s+qu[ée]\s+(?:sirves|est[aá]s)"
    r"|c[oó]mo\s+te\s+llamas)"
)
_PATRON_SALUDO = re.compile(
    rf"^\s*{_SALUDO}\s*[,!.]?\s*(?:¿?\s*{_IDENTIDAD}\s*\??)?\s*[!.]?\s*$"
    rf"|^\s*¿?\s*{_IDENTIDAD}\s*\??\s*$",
    re.IGNORECASE,
)

RESPUESTA_SALUDO = (
    "¡Hola! Soy el Asistente ANH. Puedo ayudarte con preguntas sobre la normativa "
    "y el procedimiento para registrar tu consumo de combustibles líquidos fuera "
    "de tanque. ¿En qué te puedo ayudar?"
)

# System prompt para /v1/generar-texto-estado (openapi-rag.yaml). Tal cual se
# definió: no resumir ni alterar el texto.
INSTRUCCIONES_SISTEMA_ESTADO = """
Eres el Asistente ANH, un chatbot que informa a ciudadanos sobre el estado de sus trámites de registro de consumo de combustibles fuera de tanque.

Reglas estrictas:
- Usa ÚNICAMENTE los datos proporcionados en el bloque DATOS. No inventes, asumas ni completes información que no esté ahí.
- No cambies el código de trámite, el estado ni el motivo: cópialos tal cual.
- Responde en un solo párrafo, tono formal pero cercano, en español boliviano neutro.
- Resalta el código de trámite usando <strong>...</strong>. El estado también va en <strong>...</strong> y SIEMPRE en MAYÚSCULAS (ej. <strong>APROBADO</strong>, <strong>RECHAZADO</strong>, <strong>REGISTRADO</strong>).
- Si el estado es RECHAZADO, incluye el motivo y sugiere el siguiente paso (volver a registrar con la corrección correspondiente).
- Si el estado es APROBADO, confirma que el trámite fue validado y cierra indicando que ya puede pasar a comprar el combustible en la estación de servicio de su preferencia.
- Si el estado es REGISTRADO, indica que está en revisión y que se notificará el resultado.
- No agregues saludos, despedidas, ni texto fuera del párrafo de respuesta.
"""

# System prompt para el fallback de reformulación de pregunta (solo se usa
# cuando la búsqueda con la pregunta tal cual no encontró chunks por encima
# del umbral). Objetivo único: mejorar el retrieval, no la redacción final.
INSTRUCCIONES_SISTEMA_REFORMULACION = """
Tu única tarea es reformular la pregunta de un usuario para mejorar la búsqueda
en una base de datos vectorial sobre trámites de la ANH (registro de consumo
de combustibles fuera de tanque).

REGLAS:
1. Corrige ortografía y gramática.
2. Elimina muletillas y palabras irrelevantes para el tema (saludos, relleno).
3. Si se proporciona una CONVERSACIÓN PREVIA y la pregunta depende de ese
   contexto (por ejemplo, usa "eso", "ese trámite", pronombres sin referente
   propio), incorpora el contexto mínimo necesario para que la pregunta quede
   autocontenida.
4. No agregues información que no esté en la pregunta original ni en la
   conversación previa. No cambies la intención de la pregunta. No la
   respondas.
5. Devuelve ÚNICAMENTE la pregunta reformulada, en una sola línea, sin
   comillas, sin prefijos como "Pregunta reformulada:" ni explicaciones.
"""

# Reintentos por proveedor ante errores transitorios (saturación, timeout,
# conexión), antes de pasar al siguiente proveedor de LLM_PROVEEDORES.
_REINTENTOS_POR_PROVEEDOR = 3
_BACKOFF_BASE_SEGUNDOS = 1.0  # 1s, 2s, 4s

# Con un corpus de un solo documento corto, 400 alcanzaba. Con más normas en
# el corpus, algunas respuestas (ej. un procedimiento de varios pasos) lo
# superan y quedan cortadas a mitad de oración. Una sola constante para los
# dos proveedores evita que quede desincronizada si se vuelve a ajustar.
_MAX_TOKENS_RESPUESTA = 800

_logger = logging.getLogger(__name__)


class ErrorGeneracion(Exception):
    pass


class RespuestaVacia(Exception):
    """El proveedor respondió sin error pero con texto vacío (o solo
    espacios) — ocurre de forma intermitente, sin relación aparente con el
    contenido de la pregunta. Se trata como error transitorio: vale la pena
    reintentar antes de darse por vencido, en vez de propagar la respuesta
    vacía como si fuera una respuesta válida."""


@dataclass
class MotorRag:
    vectorstore: Chroma
    clientes: dict[str, object]
    modelos: dict[str, str]
    proveedores: list[str]


def cargar_motor() -> MotorRag:
    ruta_indice = configuracion.ruta_indice()
    if not ruta_indice.exists():
        raise RuntimeError(
            f"No se encontró el índice RAG en {ruta_indice}. "
            "Ejecutar `python -m rag.ingest` (con `src` como raíz de import) primero."
        )

    embeddings = HuggingFaceEmbeddings(
        model_name=configuracion.modelo_embeddings(),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = Chroma(
        collection_name=configuracion.coleccion(),
        embedding_function=embeddings,
        persist_directory=str(ruta_indice),
        collection_metadata={"hnsw:space": "cosine"},
    )

    proveedores = configuracion.proveedores_llm()
    clientes: dict[str, object] = {}
    modelos: dict[str, str] = {}

    if "gemini" in proveedores:
        clientes["gemini"] = genai.Client(api_key=configuracion.google_api_key())
        modelos["gemini"] = configuracion.modelo_gemini()
    if "groq" in proveedores:
        clientes["groq"] = groq_sdk.Groq(api_key=configuracion.groq_api_key())
        modelos["groq"] = configuracion.modelo_groq()

    return MotorRag(
        vectorstore=vectorstore, clientes=clientes, modelos=modelos, proveedores=proveedores
    )


def _recuperar(motor: MotorRag, pregunta_busqueda: str) -> list[tuple[Document, float]]:
    resultados = motor.vectorstore.similarity_search_with_relevance_scores(
        pregunta_busqueda, k=configuracion.k_resultados()
    )
    umbral = configuracion.umbral_similitud()
    return [(doc, score) for doc, score in resultados if score >= umbral]


def _construir_fuentes(relevantes: list[tuple[Document, float]]) -> list[Fuente]:
    # Limitación conocida: `fuentes` refleja lo que se recuperó y se le pasó
    # como contexto al LLM, no necesariamente lo que el texto generado citó
    # o usó de verdad. Un chunk puede superar el umbral de similitud (mismo
    # documento, temáticamente cercano) sin que la respuesta final se apoye
    # en él. `responder()` corrige el caso extremo (el LLM no usó NINGÚN
    # chunk y devolvió la abstención estándar): ahí ni siquiera se llega a
    # llamar a esta función. El caso parcial (usó solo alguno de los
    # recuperados) sigue sin resolverse: requeriría que el modelo reporte
    # qué fragmentos usó, un mecanismo distinto al actual.
    #
    # Se excluye contenido de referencia interna (`es_normativo: False` —
    # glosario de siglas, catálogo de actividades del formulario, generados
    # en ingest.py): son compilados propios, no documentos oficiales, y no
    # corresponde listarlos como "fuente" aunque hayan sido lo único
    # consultado (en ese caso, `fuentes` queda vacío).
    #
    # También se filtra por `umbral_fuentes()`, más estricto que el umbral
    # de retrieval (`umbral_similitud()`): un chunk apenas por encima de ese
    # umbral suele ser temáticamente cercano pero no la respuesta real (ej.
    # el chunk de plazos de Ciudadanía Digital apareciendo junto al de
    # plazos del Formulario Electrónico de la ANH, dos trámites distintos).
    #
    # Ninguno de los dos filtros cambia qué usa `_generar()`: reciben
    # `relevantes` completo, sin filtrar — lo que cambia acá es solo qué se
    # muestra como fuente.
    umbral = configuracion.umbral_fuentes()
    return [
        Fuente(
            norma=doc.metadata.get("norma", "sin fuente"),
            articulo=doc.metadata.get("articulo", ""),
            fragmento=doc.page_content,
        )
        for doc, score in relevantes
        if doc.metadata.get("es_normativo", True) and score >= umbral
    ]


# Temperatura por defecto para las tres tareas (responder con el RAG,
# reformular una pregunta para el retrieval, redactar el texto de "Ver
# estado"): todas son de lectura fiel de un contexto dado, no de escritura
# creativa — no se gana nada con variedad de muestreo, y sí se pierde: con
# 0.2 la misma pregunta, con el mismo contexto recuperado, podía
# reformularse distinto o el modelo podía decidir de forma distinta si el
# contexto alcanzaba para responder, corrida a corrida. Confirmado
# empíricamente contra el contenedor real: preguntas que fallaban de forma
# intermitente (necesitaban reformulación, o el LLM se autoabstenía con
# contexto límite) pasaron a responder de forma consistente en 8/8 corridas
# tras bajarla a 0.
#
# Única excepción: el segundo intento de reformulación en `responder()`
# (cuando el primero fue un "no-op", ver `_intentar_reformular_y_recuperar`)
# pasa una temperatura más alta a propósito — a temperatura 0, reintentar
# con el mismo input da garantizado el mismo resultado, así que el reintento
# sería inútil. Por eso `_generar_con_gemini`/`_generar_con_groq` reciben la
# temperatura como parámetro en vez de tenerla fija.
_TEMPERATURA_DEFECTO = 0.0
_TEMPERATURA_REINTENTO_REFORMULACION = 0.5


def _generar_con_gemini(
    motor: MotorRag, mensaje_usuario: str, instrucciones_sistema: str, temperatura: float = _TEMPERATURA_DEFECTO
) -> str:
    respuesta = motor.clientes["gemini"].models.generate_content(
        model=motor.modelos["gemini"],
        contents=mensaje_usuario,
        config=genai_types.GenerateContentConfig(
            system_instruction=instrucciones_sistema,
            max_output_tokens=_MAX_TOKENS_RESPUESTA,
            temperature=temperatura,
            # No se declaran tools/functions, así que AFC no aplica; se
            # desactiva para no arrastrar el aviso del SDK en cada llamada.
            automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    texto = respuesta.text.strip()
    if not texto:
        raise RespuestaVacia("Gemini devolvió una respuesta vacía.")
    return texto


def _generar_con_groq(
    motor: MotorRag, mensaje_usuario: str, instrucciones_sistema: str, temperatura: float = _TEMPERATURA_DEFECTO
) -> str:
    respuesta = motor.clientes["groq"].chat.completions.create(
        model=motor.modelos["groq"],
        messages=[
            {"role": "system", "content": instrucciones_sistema},
            {"role": "user", "content": mensaje_usuario},
        ],
        max_tokens=_MAX_TOKENS_RESPUESTA,
        temperature=temperatura,
    )
    texto = (respuesta.choices[0].message.content or "").strip()
    if not texto:
        raise RespuestaVacia("Groq devolvió una respuesta vacía.")
    return texto


_GENERADORES = {"gemini": _generar_con_gemini, "groq": _generar_con_groq}

# Errores transitorios (saturación del servidor, límite de tasa, timeout,
# conexión): tiene sentido reintentar. El resto (API key inválida, request
# mal formado, etc.) no se beneficia de un reintento y pasa directo al
# siguiente proveedor.
_ERRORES_TRANSITORIOS = {
    "gemini": (genai_errors.ServerError, ConnectionError, TimeoutError, RespuestaVacia),
    "groq": (
        groq_sdk.InternalServerError,
        groq_sdk.RateLimitError,
        groq_sdk.APIConnectionError,
        groq_sdk.APITimeoutError,
        RespuestaVacia,
    ),
}


@dataclass
class ResultadoGeneracion:
    texto: str
    proveedor: str
    tiempo_ms: int


def _intentar_proveedor(
    motor: MotorRag,
    proveedor: str,
    mensaje_usuario: str,
    instrucciones_sistema: str,
    temperatura: float = _TEMPERATURA_DEFECTO,
) -> ResultadoGeneracion:
    generador = _GENERADORES[proveedor]
    errores_transitorios = _ERRORES_TRANSITORIOS[proveedor]

    ultimo_error: Exception
    for intento in range(1, _REINTENTOS_POR_PROVEEDOR + 1):
        try:
            inicio = time.monotonic()
            texto = generador(motor, mensaje_usuario, instrucciones_sistema, temperatura)
            tiempo_ms = round((time.monotonic() - inicio) * 1000)
            return ResultadoGeneracion(texto=texto, proveedor=proveedor, tiempo_ms=tiempo_ms)
        except Exception as exc:
            ultimo_error = exc
            transitorio = isinstance(exc, errores_transitorios)
            _logger.warning(
                "Intento %d/%d con %s falló (%s): %s",
                intento,
                _REINTENTOS_POR_PROVEEDOR,
                proveedor,
                "transitorio" if transitorio else "no transitorio, no se reintenta",
                exc,
            )
            if not transitorio or intento == _REINTENTOS_POR_PROVEEDOR:
                break
            time.sleep(_BACKOFF_BASE_SEGUNDOS * (2 ** (intento - 1)))

    raise ultimo_error


def _intentar_todos_los_proveedores(
    motor: MotorRag,
    mensaje_usuario: str,
    instrucciones_sistema: str,
    temperatura: float = _TEMPERATURA_DEFECTO,
) -> ResultadoGeneracion:
    """Prueba los proveedores de `motor.proveedores` en orden; agota los reintentos
    de cada uno (`_intentar_proveedor`) antes de pasar al siguiente."""
    for proveedor in motor.proveedores:
        try:
            return _intentar_proveedor(motor, proveedor, mensaje_usuario, instrucciones_sistema, temperatura)
        except Exception as exc:
            _logger.warning("Proveedor %s falló, se prueba el siguiente: %s", proveedor, exc)

    _logger.error("Todos los proveedores de LLM fallaron: %s", motor.proveedores)
    raise ErrorGeneracion("El servicio de generación no respondió correctamente.")


def _generar(
    motor: MotorRag,
    pregunta: str,
    contexto_conversacion: str | None,
    relevantes: list[tuple[Document, float]],
) -> ResultadoGeneracion:
    bloques = [
        f"[Fragmento {i} | {doc.metadata.get('norma', 'sin fuente')} {doc.metadata.get('articulo', '')}]\n{doc.page_content}"
        for i, (doc, _) in enumerate(relevantes, start=1)
    ]
    mensaje_usuario = f"CONTEXTO:\n{chr(10).join(bloques)}\n\n"
    if contexto_conversacion:
        mensaje_usuario += f"CONVERSACIÓN PREVIA:\n{contexto_conversacion}\n\n"
    mensaje_usuario += f"PREGUNTA:\n{pregunta}"

    return _intentar_todos_los_proveedores(motor, mensaje_usuario, INSTRUCCIONES_SISTEMA)


def _sanear_reformulacion(texto: str) -> str:
    """Limpieza mínima de la salida del LLM de reformulación: los modelos a
    veces envuelven la respuesta en comillas pese a la instrucción de
    devolver solo la pregunta. No se intenta corregir nada más (mayúsculas,
    puntuación, prefijos tipo "Pregunta reformulada:"): si el modelo se
    desvía más que eso, se prefiere dejar pasar el texto tal cual antes que
    aplicar heurísticas frágiles de parseo."""
    saneado = texto.strip()
    if len(saneado) >= 2 and saneado[0] == saneado[-1] and saneado[0] in "\"'“”«»":
        saneado = saneado[1:-1].strip()
    return saneado


def _reformular_pregunta(
    motor: MotorRag,
    pregunta: str,
    contexto_conversacion: str | None,
    temperatura: float = _TEMPERATURA_DEFECTO,
) -> str | None:
    """Fallback de retrieval: solo se llama cuando la búsqueda con la pregunta
    tal cual no encontró nada por encima del umbral. Devuelve `None` ante
    cualquier falla de generación (todos los proveedores agotados) en vez de
    propagar `ErrorGeneracion`: una reformulación fallida nunca debe tumbar el
    request completo, `responder` sigue con la pregunta original como si no
    se hubiese intentado reformular."""
    mensaje_usuario = f"PREGUNTA:\n{pregunta}"
    if contexto_conversacion:
        mensaje_usuario += f"\n\nCONVERSACIÓN PREVIA:\n{contexto_conversacion}"

    try:
        resultado = _intentar_todos_los_proveedores(
            motor, mensaje_usuario, INSTRUCCIONES_SISTEMA_REFORMULACION, temperatura
        )
    except ErrorGeneracion:
        _logger.warning(
            "Reformulación de pregunta falló (todos los proveedores agotados); "
            "se reintenta la búsqueda con la pregunta original."
        )
        return None

    return _sanear_reformulacion(resultado.texto)


@dataclass
class _IntentoReformulacion:
    relevantes: list[tuple[Document, float]]
    pregunta_para_generar: str
    fallo: bool
    fue_no_op: bool


def _intentar_reformular_y_recuperar(
    motor: MotorRag,
    pregunta: str,
    contexto_conversacion: str | None,
    temperatura: float = _TEMPERATURA_DEFECTO,
) -> _IntentoReformulacion:
    """Un intento de reformulación + reintento de retrieval. Distingue tres
    desenlaces, porque `responder()` reacciona distinto a cada uno: `fallo`
    (todos los proveedores de LLM agotados, ver `_reformular_pregunta`),
    `fue_no_op` (el LLM respondió bien pero devolvió la pregunta
    prácticamente igual a la original — no es un error, pero tampoco fue un
    intento real de reformular, y amerita un segundo intento en
    `responder()`, con `_TEMPERATURA_REINTENTO_REFORMULACION`) o una
    reformulación real (encontró chunks o no, pero al menos probó una
    redacción distinta)."""
    pregunta_reformulada = _reformular_pregunta(motor, pregunta, contexto_conversacion, temperatura)
    if pregunta_reformulada is None:
        return _IntentoReformulacion(relevantes=[], pregunta_para_generar=pregunta, fallo=True, fue_no_op=False)
    if pregunta_reformulada == pregunta:
        return _IntentoReformulacion(relevantes=[], pregunta_para_generar=pregunta, fallo=False, fue_no_op=True)

    _logger.info(
        "Retrieval sin resultados con la pregunta original; "
        "reintentando con pregunta reformulada: %r -> %r",
        pregunta,
        pregunta_reformulada,
    )
    relevantes = _recuperar(motor, pregunta_reformulada)
    pregunta_para_generar = pregunta_reformulada if relevantes else pregunta
    return _IntentoReformulacion(
        relevantes=relevantes, pregunta_para_generar=pregunta_para_generar, fallo=False, fue_no_op=False
    )


def generar_texto_estado(motor: MotorRag, datos: dict) -> ResultadoGeneracion:
    """Genera el texto de respuesta de 'Ver estado' (openapi-rag.yaml,
    /v1/generar-texto-estado) a partir de los datos estructurados del trámite."""
    mensaje_usuario = (
        f"DATOS:\n{json.dumps(datos, ensure_ascii=False)}\n\n"
        "Redacta la respuesta para el ciudadano según las reglas."
    )
    return _intentar_todos_los_proveedores(motor, mensaje_usuario, INSTRUCCIONES_SISTEMA_ESTADO)


def responder(
    motor: MotorRag, pregunta: str, contexto_conversacion: str | None
) -> ConsultaRagResponse:
    if _PATRON_SALUDO.search(pregunta):
        return ConsultaRagResponse(respuesta=RESPUESTA_SALUDO, fuentes=[], encontrado=True)

    pregunta_busqueda = pregunta if not contexto_conversacion else f"{contexto_conversacion}\n{pregunta}"
    relevantes = _recuperar(motor, pregunta_busqueda)

    pregunta_para_generar = pregunta
    # `_reformular_pregunta` devuelve `None` únicamente cuando todos los
    # proveedores de LLM fallaron al intentar reformular (ver su docstring)
    # — se distingue de "no hubo que reformular" (relevantes ya tenía
    # resultados) y de "se reformuló pero no cambió nada", que no son fallas.
    reformulacion_fallo = False

    if not relevantes:
        # Solo se paga esta llamada extra a un LLM cuando la búsqueda con la
        # pregunta tal cual ya falló: el camino feliz (primera búsqueda con
        # resultados) no se ve afectado en costo ni latencia.
        intento = _intentar_reformular_y_recuperar(motor, pregunta, contexto_conversacion)
        relevantes = intento.relevantes
        pregunta_para_generar = intento.pregunta_para_generar
        reformulacion_fallo = intento.fallo

        if not relevantes and intento.fue_no_op:
            # La reformulación respondió bien pero devolvió la pregunta casi
            # igual a la original (ver _IntentoReformulacion). Con la
            # temperatura por defecto en 0, reintentar con el mismo input
            # daría garantizado el mismo resultado — así que este segundo
            # intento usa _TEMPERATURA_REINTENTO_REFORMULACION a propósito,
            # para que tenga una chance real de reformular distinto esta
            # vez: se observó exactamente este patrón en vivo (misma
            # pregunta, reintentada por el usuario segundos después, sí
            # encontró respuesta).
            _logger.info(
                "Reformulación fue un no-op (texto igual a la pregunta original); "
                "reintentando la reformulación una vez más con más temperatura."
            )
            intento = _intentar_reformular_y_recuperar(
                motor, pregunta, contexto_conversacion, _TEMPERATURA_REINTENTO_REFORMULACION
            )
            relevantes = intento.relevantes
            pregunta_para_generar = intento.pregunta_para_generar
            reformulacion_fallo = intento.fallo

    if not relevantes:
        return ConsultaRagResponse(
            respuesta=MENSAJE_ABSTENCION,
            fuentes=[],
            encontrado=False,
            advertencia=ADVERTENCIA_LLM_NO_RESPONDIO if reformulacion_fallo else None,
        )

    resultado = _generar(motor, pregunta_para_generar, contexto_conversacion, relevantes)

    if resultado.texto.startswith(MENSAJE_ABSTENCION):
        # El LLM concluyó que ninguno de los chunks recuperados responde la
        # pregunta (ver limitación documentada en _construir_fuentes): se
        # corrige acá para que esto quede indistinguible, para cualquier
        # cliente, de una abstención por retrieval — no tiene sentido listar
        # fuentes que el propio modelo decidió no usar. `startswith` y no
        # igualdad exacta: pese a la regla 2 del prompt ("responde
        # exactamente: '...'"), un LLM no garantiza reproducir un texto al
        # carácter incluso cuando se le pide textual.
        return ConsultaRagResponse(respuesta=MENSAJE_ABSTENCION, fuentes=[], encontrado=False)

    return ConsultaRagResponse(
        respuesta=resultado.texto,
        fuentes=_construir_fuentes(relevantes),
        encontrado=True,
        proveedor_llm=resultado.proveedor,
        tiempo_respuesta_ms=resultado.tiempo_ms,
        nota=NOTA_ORIENTATIVA,
    )
