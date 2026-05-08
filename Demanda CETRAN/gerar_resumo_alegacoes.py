import requests

def resumir_defesa_ia(texto_pdf):
    """
    Envia o texto bruto do PDF para o Ollama e extrai os argumentos do recorrente.
    """
    prompt = f"""
    Abaixo está o texto extraído de um processo de multa do DETRAN. 
    Identifique os argumentos de defesa usados pelo recorrente e resuma-os em uma 
    única frase formal iniciada por 'O recorrente alega...'.
    
    TEXTO:
    {texto_pdf[:4000]} # Limitamos o texto para não estourar o contexto
    """
    
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3:8b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1} # Baixa temperatura para ser fiel ao texto
        }, timeout=60)
        
        return response.json().get("response", "").strip()
    except:
        return "Não foi possível resumir a alegação automaticamente."