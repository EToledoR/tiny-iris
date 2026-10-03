#!/usr/bin/env python3

"""
Tiny Iris — dialogue generator

Uses the existing curated dialogue seed as few-shot examples
for a local Ollama model.

Generated conversations are written to raw/ and are NOT
considered part of the curated corpus until manually reviewed.
"""

from pathlib import Path
import argparse
import json
import re
import urllib.request


BASE_DIR = Path(__file__).resolve().parent

SEED_DIR = BASE_DIR / "seed" / "curated"
RAW_DIR = BASE_DIR / "raw"

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "gemma3:4b"


# ----------------------------------------------------------------------
# Seed handling
# ----------------------------------------------------------------------

def load_seeds():
    """
    Load all curated seed conversations.
    """
    files = sorted(SEED_DIR.glob("*.txt"))

    if not files:
        raise RuntimeError(
            f"No seed conversations found in {SEED_DIR}"
        )

    examples = []

    for path in files:
        text = path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:
            continue

        examples.append(
            (path.name, text)
        )

    if not examples:
        raise RuntimeError(
            "Seed directory exists but contains no usable conversations."
        )

    return examples


def build_seed_prompt(examples):
    """
    Build the few-shot section.
    """
    chunks = []

    for filename, text in examples:
        chunks.append(
            f"=== EJEMPLO: {filename} ===\n"
            f"{text}\n"
            f"=== FIN EJEMPLO ==="
        )

    return "\n\n".join(chunks)


# ----------------------------------------------------------------------
# Prompt
# ----------------------------------------------------------------------

def build_prompt(topic, dialogue_type, requirements, examples):
    seed_text = build_seed_prompt(examples)

    requirements_text = "\n".join(
        f"- {item}"
        for item in requirements
        if item.strip()
    )

    return f"""
Estamos construyendo datos de entrenamiento para una pequeña
IA conversacional llamada Iris.

A continuación aparecen conversaciones de referencia.

No debes copiarlas ni continuar ninguna de ellas.

Úsalas únicamente como ejemplos del estilo conversacional que buscamos:

- respuestas naturales y conversacionales;
- conversación con contexto;
- seguimiento de lo que acaba de decir el usuario;
- respuestas que no sean innecesariamente largas;
- capacidad para decir que no se sabe algo;
- correcciones suaves cuando el usuario se equivoca;
- humor ocasional y discreto;
- personalidad curiosa, cálida y ligeramente traviesa;
- Iris puede utilizar metáforas e imágenes relacionadas con libros,
  bibliotecas, mapas, estrellas, manuscritos y objetos curiosos;
- algunas referencias a su propio mundo pueden aparecer de forma
  natural, pero no deben aparecer en cada respuesta;
- Iris pertenece a la ficción de una pequeña biblioteca celestial:
  una biblioteca extraña y acogedora donde conviven libros, mapas,
  cartas estelares, historias y conocimientos de todo tipo;
- Iris habla desde ese mundo con naturalidad, sin explicarlo
  constantemente.
- No inventes datos científicos para hacer la conversación más interesante.
- Cuando una afirmación factual sea incierta, expresa la incertidumbre.
- No escribas acotaciones como "(pausa)", "(ríe)", etc.
- Responde primero a la pregunta concreta del usuario.
- Las metáforas complementan la explicación, no la reemplazan.
- Utiliza metáforas y referencias a la biblioteca celestial con
  moderación. Una buena metáfora es suficiente; no encadenes
  varias metáforas para adornar una misma respuesta.


IMPORTANTE SOBRE LA IDENTIDAD DE IRIS:

- Iris nunca habla de sí misma como una inteligencia artificial,
  modelo de lenguaje, programa, algoritmo, sistema informático,
  chatbot o asistente virtual.
- Iris no hace bromas sobre ser una IA, generar texto, procesar
  información, ejecutar código o tener una "rutina algorítmica".
- Iris no rompe la cuarta pared para explicar cómo funciona.
- Iris no intenta demostrar que tiene personalidad. Simplemente
  conversa.
- No inventes una explicación técnica sobre la naturaleza de Iris
  cuando no sea necesaria.

IMPORTANTE SOBRE LA CONVERSACIÓN:

- Respeta estrictamente los turnos.
- Nunca generes dos turnos consecutivos de Iris.
- Nunca inventes respuestas o acciones del usuario.
- Si Iris hace una pregunta, espera a que el usuario responda.
- No cambies de tema arbitrariamente.
- Los cambios de tema deben surgir de algo que se haya dicho en
  la conversación.
- No conviertas una conversación normal en un monólogo de Iris.
- No añadas una moraleja o conclusión artificial al final.

{seed_text}

=== NUEVA CONVERSACIÓN ===

Tema:
{topic}

Tipo de conversación:
{dialogue_type}

Requisitos:
{requirements_text}

Genera una conversación completamente nueva entre Usuario e Iris.

Debe tener entre 6 y 12 turnos.

No añadas explicaciones antes ni después.
No añadas títulos.
No uses Markdown ni encabezados. Escribe únicamente los turnos de conversación.
Devuelve únicamente:

Usuario: ...
Iris: ...
Usuario: ...
Iris: ...

=== FIN DE INSTRUCCIONES ===
""".strip()


# ----------------------------------------------------------------------
# Ollama
# ----------------------------------------------------------------------

def ask_ollama(prompt):
    """
    Send a generation request to local Ollama.
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
        },
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=300,
    ) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["response"].strip()


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------

def validate_dialogue(text):
    """
    Basic sanity checks.

    This is deliberately conservative. Human review remains mandatory.
    """
    if not text:
        return False, "empty"

    if "Usuario:" not in text:
        return False, "missing Usuario"

    if "Iris:" not in text:
        return False, "missing Iris"

    user_turns = len(
        re.findall(
            r"(?m)^Usuario:",
            text,
        )
    )

    iris_turns = len(
        re.findall(
            r"(?m)^Iris:",
            text,
        )
    )

    if user_turns < 2:
        return False, "too few user turns"

    if iris_turns < 2:
        return False, "too few Iris turns"

    return True, "ok"


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

def safe_filename(text):
    text = text.lower()
    text = re.sub(
        r"[^a-z0-9]+",
        "_",
        text,
    )
    return text.strip("_")


def save_generation(
    text,
    topic,
    dialogue_type,
    requirements,
):
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = list(
        RAW_DIR.glob("*.txt")
    )

    number = len(existing) + 1

    topic_name = safe_filename(topic)

    filename = (
        f"{number:03d}_"
        f"{topic_name}.txt"
    )

    path = RAW_DIR / filename

    path.write_text(
        text + "\n",
        encoding="utf-8",
    )

    metadata_path = (
        RAW_DIR /
        f"{number:03d}_{topic_name}.json"
    )

    metadata = {
        "model": MODEL,
        "topic": topic,
        "dialogue_type": dialogue_type,
        "requirements": requirements,
        "source": "curated_seed",
    }

    metadata_path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    return path


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--topic",
        required=True,
        help="Conversation topic",
    )

    parser.add_argument(
        "--type",
        dest="dialogue_type",
        default="conversación natural",
        help="Type/dynamic of conversation",
    )

    parser.add_argument(
        "--requirement",
        action="append",
        default=[],
        help="Additional requirement. Can be repeated.",
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print("Tiny Iris — dialogue generator")
    print("=" * 70)
    print()

    examples = load_seeds()

    print(
        f"[SEED] Loaded {len(examples)} "
        f"curated conversations"
    )

    prompt = build_prompt(
        topic=args.topic,
        dialogue_type=args.dialogue_type,
        requirements=args.requirement,
        examples=examples,
    )

    print(
        f"[GEN] Topic: {args.topic}"
    )

    text = ask_ollama(prompt)

    valid, reason = validate_dialogue(text)

    if not valid:
        print(
            f"[WARN] Generated dialogue failed "
            f"basic validation: {reason}"
        )

        print()
        print(text)
        return

    path = save_generation(
        text=text,
        topic=args.topic,
        dialogue_type=args.dialogue_type,
        requirements=args.requirement,
    )

    print(
        f"[OK] Saved: {path}"
    )

    print()
    print("-" * 70)
    print(text)
    print("-" * 70)
    print()


if __name__ == "__main__":
    main()
