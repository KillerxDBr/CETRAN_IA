from datetime import datetime

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

    timeout = 180

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.Timeout:
        print(f"ERRO: Timeout ao chamar Ollama ({timeout})")
        return "{}"
    except requests.exceptions.ConnectionError:
        print("ERRO: Não foi possível conectar ao Ollama. Verifique se está rodando.")
        return "{}"
    except Exception as e:
        print(f"ERRO ao chamar Ollama: {e}")
        return "{}"


def mapear_e_analisar_processo_ia(texto_bruto):
    if not texto_bruto or len(texto_bruto) < 50:
        return {}

    campos = {
        "recorrente": "Nome completo do interessado/proprietário do veículo",
        "jari_origem": "Nome da JARI que julga o recurso (ex: JARI Municipal de Cuiaba, DETRAN)",
        "legitimidade": "Qualificação do recorrente: Proprietário ou Condutor",
        "veiculo_completo": "Marca, modelo E cor do veículo. Exemplos: 'Toyota Corolla Prata', 'Fiat Mobi Vermelho', 'Honda Civic Cinza'. NUNCA use a placa aqui.",
        "local_hora": "Endereço completo da infração com data e hora no formato: <Local da Infração>, <Cidade>-<Estado>, <DD/MM/YYYY> <HH:mm>",
        "tipificacao": "Artigo do CTB infringido com descrição (ex: Art. 218, Inciso I do CTB - Ultrapassar em faixa de pedestre)",
        "valor_multa": "Valor da multa se mencionada (ex: R$ 293,47 ou  se não mencionada)",
        "pontos_cnh": "Pontos na CNH se mencionados (ex: 7 pontos ou  se não mencionados)",
        "artigo_ctb": "Somente o artigo do CTB (ex: Art. 218)",
        "data_autuaçao": "Data em que foi efetuada a Autuação da infração no formato DD/MM/YYYY",
        "data_notificacao": "Data da Postagem da Notificação da Autuação, no formato DD/MM/YYYY",
    }

    # Prompt melhorado com instruções claras e sem ambiguidade
    # ATENÇÃO: NÃO confunda PLACA (ex: KAU3252) com VEÍCULO (ex: Toyota Corolla)
    prompt = f"""Você é um analisador de processos de trânsito do DETRAN-MT.
Sua tarefa é extrair informações estruturadas do texto do processo abaixo.
Responda apenas com informações presentes no texto. Se um campo não existir, use string vazia "".

IMPORTANTE: Não confunda PLACA (código como KAU3252, ABC1234) com VEÍCULO (marca/modelo/cor como Toyota Corolla Prata).

Analise o texto e extraia:

TEXTO DO PROCESSO:
{texto_bruto}

Responda EXCLUSIVAMENTE em JSON válido (sem markdown, sem comentários):
{{
{"\n".join([f'    "{k}": "{v}"{'' if i == len(campos) else ','}' for i, (k, v) in enumerate(campos.items(), 1)])}
}}
"""

    dt = datetime.now()
    with open(f"prompts/prompt-{dt.strftime('%d_%m_%Y-%H_%M_%S')}.txt", "xb") as f:
        f.write(prompt.encode())

    print(f"{len(prompt) = }")

    # res = _chamar_ollama(prompt, json_mode=True)
    res = '{}'
    try:
        dados = json.loads(res)
        # Garante que todas as chaves existem
        for campo in campos.keys():
            if campo not in dados:
                dados[campo] = ""
        return dados
    except json.JSONDecodeError as e:
        print(f"ERRO: Resposta da IA não é JSON válido: {e}")
        print(f"Resposta recebida: {res[:500]}")
        return {}
