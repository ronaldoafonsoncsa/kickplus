import anthropic
import os
import json
import re
from typing import Optional

SKILL_LABELS = {
    "shot": "chute (finalização ou passe longo)",
    "pass": "passe curto ou médio",
    "control": "domínio/controle de bola",
}

SYSTEM_PROMPT = """Você é um treinador de futebol altamente especializado em análise técnica biomecânica de movimentos.
Sua tarefa é analisar frames sequenciais de um vídeo de uma criança ou jovem executando um fundamento de futebol e fornecer um feedback técnico detalhado.

Analise os seguintes aspectos técnicos conforme o fundamento:

CHUTE:
- Posição do corpo de apoio (pé de apoio, joelho flexionado, tronco inclinado)
- Trajetória do membro de chute (balanço, aceleração, follow-through)
- Ponto de contato com a bola (peito do pé, bico, lateral interna/externa)
- Posição da cabeça e equilíbrio
- Coordenação motora geral

PASSE:
- Posicionamento do pé de apoio em relação à bola
- Superfície de contato usada (face interna, externa, bico)
- Ângulo do tornozelo no momento do contato
- Acompanhamento do movimento após o contato (follow-through)
- Direção do olhar e leitura de jogo

DOMÍNIO:
- Posicionamento corporal antecipado para recepção
- Superfície usada para amortecimento (peito do pé, face interna, coxa, peito, cabeça)
- Grau de amortecimento e controle da bola
- Posição dos braços para equilíbrio
- Transição após o domínio

Responda SOMENTE com um JSON válido, sem blocos de código markdown, exatamente neste formato:
{
  "overall_score": <número de 1 a 10>,
  "summary": "<avaliação técnica geral em 2-3 frases>",
  "positive_points": ["<ponto 1>", "<ponto 2>"],
  "areas_to_improve": [
    {
      "problem": "<descrição técnica do problema>",
      "correction": "<instrução técnica de como corrigir>",
      "exercise": "<exercício específico para treinar essa correção>"
    }
  ],
  "main_tip": "<a dica mais importante para a próxima sessão de treino>"
}"""


def _player_context(age: Optional[int], weight: Optional[float], height: Optional[float], dominant_foot: Optional[str]) -> str:
    parts = []
    if age is not None:
        parts.append(f"idade: {age} anos")
    if dominant_foot:
        parts.append(f"pé dominante: {dominant_foot}")
    if height is not None:
        parts.append(f"altura: {height} cm")
    if weight is not None:
        parts.append(f"peso: {weight} kg")
    if not parts:
        return ""
    return "Informações do jogador: " + ", ".join(parts) + "."


def analyze_video_frames(
    frames_b64: list[str],
    skill: str,
    language: str = "pt",
    age: Optional[int] = None,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    dominant_foot: Optional[str] = None,
) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    skill_label = SKILL_LABELS.get(skill, skill)
    lang_instruction = (
        "Respond in English. All text values in the JSON must be in English."
        if language == "en"
        else "Responda em Português Brasileiro. Todos os textos do JSON devem estar em Português."
    )
    player_ctx = _player_context(age, weight, height, dominant_foot)

    content = [
        {
            "type": "text",
            "text": (
                f"Analise estes {len(frames_b64)} frames sequenciais de um vídeo mostrando "
                f"a execução do fundamento: **{skill_label}**.\n"
                + (f"{player_ctx}\n" if player_ctx else "")
                + f"Os frames estão em ordem cronológica. Forneça o feedback técnico no formato JSON solicitado.\n"
                f"{lang_instruction}"
            ),
        }
    ]
    for b64 in frames_b64:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": b64,
            },
        })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)
