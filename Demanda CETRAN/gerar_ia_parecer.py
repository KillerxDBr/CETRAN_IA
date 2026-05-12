import requests
import json


def _chamar_ollama(prompt, json_mode=False):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3:8b",
        "prompt": prompt,
        "stream": False,
        "format": "json" if json_mode else "",
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        }
    }
    # return "Skipped"
    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.Timeout:
        print("ERRO: Timeout ao chamar Ollama (180s)")
        return "{}"
    except requests.exceptions.ConnectionError:
        print("ERRO: Não foi possível conectar ao Ollama. Verifique se está rodando.")
        return "{}"
    except Exception as e:
        print(f"ERRO ao chamar Ollama: {e}")
        return "{}"


def mapear_e_analisar_processo_ia(texto_bruto):
    if not texto_bruto or len(texto_bruto.strip()) < 50:
        return {}

    # Prompt melhorado com instruções claras e sem ambiguidade
    # ATENÇÃO: NÃO confunda PLACA (ex: KAU3252) com VEÍCULO (ex: Toyota Corolla)
    prompt = f"""Você é um analisador de processos de trânsito do DETRAN-MT.
Sua tarefa é extrair informações estruturadas do texto do processo abaixo.
Responda apenas com informações presentes no texto. Se um campo não existir, use string vazia "".

IMPORTANTE: Não confunda PLACA (código como KAU3252, ABC1234) com VEÍCULO (marca/modelo/cor como Toyota Corolla Prata).

Analise o texto e extraia:

TEXTO DO PROCESSO:
{texto_bruto[:10000]}

Responda EXCLUSIVAMENTE em JSON válido (sem markdown, sem comentários):
{{
    "recorrente": "Nome completo do interessado/proprietário do veículo",
    "jari_origem": "Nome da JARI que julga o recurso (ex: JARI Municipal de Cuiaba, DETRAN)",
    "legitimidade": "Qualificação do recorrente: Proprietário ou Condutor",
    "veiculo_completo": "Marca, modelo E cor do veículo. Exemplos: 'Toyota Corolla Prata', 'Fiat Mobi Vermelho', 'Honda Civic Cinza'. NUNCA use a placa aqui.",
    "local_hora": "Endereço completo da infração com data e hora (ex: Av. Histórica, 100 - Centro, Cuiaba/MT, 15/03/2025 14:30)",
    "tipificacao": "Artigo do CTB infringido com descrição (ex: Art. 218, Inciso I do CTB - Ultrapassar em faixa de pedestre)",
    "valor_multa": "Valor da multa se mencionada (ex: R$ 293,47 ou "" se não mencionada)",
    "pontos_cnh": "Pontos na CNH se mencionados (ex: 7 pontos ou "" se não mencionados)",
    "artigo_ctb": "Somente o artigo do CTB (ex: Art. 218)"
}}
"""

    res = _chamar_ollama(prompt, json_mode=True)

    try:
        dados = json.loads(res)
        # Garante que todas as chaves existem
        campos_esperados = [
            "recorrente", "jari_origem", "legitimidade", "veiculo_completo",
            "local_hora", "tipificacao", "valor_multa", "pontos_cnh", "artigo_ctb"
        ]
        for campo in campos_esperados:
            if campo not in dados:
                dados[campo] = ""
        return dados
    except json.JSONDecodeError as e:
        print(f"ERRO: Resposta da IA não é JSON válido: {e}")
        print(f"Resposta recebida: {res[:500]}")
        return {}
