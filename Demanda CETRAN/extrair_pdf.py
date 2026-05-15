import pdfplumber
import re
from datetime import datetime


def _extrair_cpf(texto):
    """Extrai CPF do texto."""
    cpf_match = re.search(r"CPF[^\d]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", texto, re.IGNORECASE)
    if cpf_match:
        return cpf_match.group(1)
    return ""


def _extrair_cnpj(texto):
    """Extrai CNPJ do texto."""
    cnpj_match = re.search(r"CNPJ[^\d]*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})", texto, re.IGNORECASE)
    if cnpj_match:
        return cnpj_match.group(1)
    return ""


def _extrair_valor_multa(texto):
    """Extrai valor da multa."""
    valores = re.findall(r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})", texto)
    for val in valores:
        try:
            num = val.replace(".", "").replace(",", ".")
            if 50 < float(num) < 30000:
                return f"R$ {val}"
        except:
            pass
    return ""


def _extrair_pontos(texto):
    """Extrai pontos na CNH."""
    pontos_match = re.search(r"(\d+)\s*(?:ponto|pontos)\s*(?:na\s*)?(?:CNH|carteira)", texto, re.IGNORECASE)
    if pontos_match:
        return pontos_match.group(1)
    return ""


def _extrair_artigo_ctb(texto):
    """Extrai artigo do CTB mencionado."""
    artigos = re.findall(r"(?:Art\.?\s*)?(\d{3})\s*(?:[\/,]\s*\S+)?\s*(?:do\s*CTB)?", texto)
    for art in artigos:
        num = int(art)
        if 161 <= num <= 302:
            return f"Art. {art} do CTB"
    return ""


def _limpar_nome(texto):
    """Limpa nome do recorrente."""
    if not texto:
        return ""
    # Remove quebras de linha excessivas
    texto = re.sub(r"\s+", " ", texto)
    # Limita tamanho
    if len(texto) > 80:
        texto = texto[:80]
    return texto.strip()


def _extrair_veiculo(texto):
    """Extrai marca, modelo e cor do veículo de múltiplas formas."""
    # Padrão 1: "Veículo: MARCA/MODELO/COR" ou similar
    veiculo_match = re.search(
        r"(?:Ve[ií]culo|Veic\.?)\s*[:\-]?\s*([A-Za-z]{3,}\s*[A-Za-z0-9\s]+?)(?:\s*/|\s*-|\s*\n|CPF|PLACA|CHASSI|PROPRIETÁRIO)",
        texto, re.IGNORECASE
    )
    if veiculo_match:
        return veiculo_match.group(1).strip()

    # Padrão 2: "Marca/Modelo: ... / Cor: ..."
    marca_match = re.search(
        r"(?:Marca|Modelo)\s*[:\-]?\s*([A-Za-z\s]+?)(?:/|\s*-|\s*Cor|\n)",
        texto, re.IGNORECASE
    )
    cor_match = re.search(
        r"(?:Cor|Cor\s*do\s*Ve[ií]culo)\s*[:\-]?\s*([A-Za-z]+)",
        texto, re.IGNORECASE
    )
    if marca_match:
        marca = marca_match.group(1).strip()
        cor = cor_match.group(1).strip() if cor_match else ""
        return f"{marca} / {cor}" if cor else marca

    # Padrão 3: Busca linha que contenha "VW", "FIAT", "TOYOTA", "FORD", "GM", "HONDA", etc
    marcas_validas = ["VW", "FIAT", "TOYOTA", "FORD", "GM", "HONDA", "HYUNDAI", "KIA", "JEEP", "RENAULT",
                      "CHEVROLET", "MERCEDES", "BMW", "AUDI", "NISSAN", "MITSUBISHI", "VOLKSWAGEN", "PEUGEOT"]
    for marca in marcas_validas:
        pattern = rf"\b{marca}\b\s+([A-Za-z0-9\s]+?)(?:\s*/|\s*-|\s*\d{{4}}|\s*Cor|\n)"
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            modelo = match.group(1).strip()
            # Procura cor nesta linha
            cor_pattern = rf"{marca}.*?(?:PRETO|BRANCO|PRATA|VERMELHO|AZUL|CINZA|VERDE|AMARELO|GRIS)",
            cor_match = re.search(cor_pattern, texto, re.IGNORECASE)
            cor = ""
            if cor_match:
                cor_encontrada = re.search(r"(PRETO|BRANCO|PRATA|VERMELHO|AZUL|CINZA|VERDE|AMARELO|GRIS)", cor_match.group(0), re.IGNORECASE)
                if cor_encontrada:
                    cor = cor_encontrada.group(1).title()
            return f"{marca} {modelo}" + (f" / {cor}" if cor else "")

    # Padrão 4: "Espécie/Tipo: Automobile" - indica que é um veículo
    if "Automóvel" in texto or "AUTOMOVEL" in texto.upper():
        # Tenta encontrar alguma menção de veículo
        veic_lines = [l for l in texto.split("\n") if any(m in l.upper() for m in marcas_validas)]
        if veic_lines:
            return veic_lines[0].strip()

    return ""


def _extrair_veiculo2(texto: str):
    for line in texto.split("\n"):
        if line.startswith("2.2 - MARCA/MODELO:"):
            line = line.removeprefix("2.2 - MARCA/MODELO:").split("-")[0].strip()
            return line
    return _extrair_veiculo(texto)


def extrair_dados_detran_pdf(caminho_pdf):
    dados = {
        "processo": "",
        "recorrente": "",
        "placa": "",
        "ait_numero": "",
        "cpf": "",
        "cnpj": "",
        "valor_multa": "",
        "pontos_cnh": "",
        "artigo_ctb": "",
        "veiculo_completo": "",
    }
    texto_completo = ""

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text() or ""
                texto_completo += texto_pagina + "\n"

        prefixes = [
            "Autenticado com senha por",
            "https://www.sigadoc.mt.gov.br/",
        ]
        suffixes = [
            "PACNARTED",
            "consulta à autenticidade em",
        ]
        ignore = [
            "DETRAN",
            "G",
            "overno",
            "de M",
            "ato Grosso",
            "overno d",
            "e Mato Grosso",
        ]
        tmp = []
        for x in texto_completo.strip().split("\n"):
            x = x.strip()
            if len(x) < 2:
                continue
            if x in ignore:
                continue

            skip = False
            for p in prefixes:
                if x.startswith(p):
                    skip = True
            if skip:
                continue

            for s in suffixes:
                if x.endswith(s):
                    skip = True
            if skip:
                continue

            t = x.split(" ")
            if (len(t) == 4) and (t[0] == "Página") and (t[2] == "de" or t[2] == "/"):
                continue

            tmp.append(x)

        texto_completo = "\n".join(tmp).strip()

        # 1. Processo SIGADOC (ex: DETRAN-PRO-2025/30490)
        proc = re.search(r"(DETRAN-PRO-\d{4}/\d+)", texto_completo)
        if proc:
            dados["processo"] = proc.group(1)

        # 2. AIT (ex: F433623812)
        ait = re.search(r"\b([A-Z]{1}\d{9})\b", texto_completo)
        if ait:
            dados["ait_numero"] = ait.group(1)

        # 3. PLACA (ex: KAU3252)
        placas = re.findall(r"\b([A-Z]{3}-?\d[A-Z0-9]\d{2})\b", texto_completo)
        for p in placas:
            limpa = p.replace("-", "")
            if "202" not in limpa and "PRO" not in limpa and len(limpa) == 7:
                dados["placa"] = limpa.upper()
                break

        # 4. RECORRENTE - Busca em múltiplos padrões
        # Padrão 1: Interessado:
        rec_match = re.search(r"Interessado:\s*([A-ZÀ-Ü\s\.]+)", texto_completo, re.IGNORECASE)
        if rec_match:
            nome_bruto = rec_match.group(1).strip()
            nome_limpo = re.split(r"CPF|CNPJ|Resumo|Assunto|\n", nome_bruto, flags=re.IGNORECASE)[0].strip()
            dados["recorrente"] = _limpar_nome(nome_limpo)

        # Padrão 2: Nome do Interessado:
        if not dados["recorrente"]:
            rec_match = re.search(r"(?:Nome\s*(?:do\s*)?Interessado|Interessado\s*a\s*(?:presente\s*)?(?:Recurso\s*)?)\s*[:\-]?\s*([A-ZÀ-Ü\s\.]+)", texto_completo, re.IGNORECASE)
            if rec_match:
                nome_bruto = rec_match.group(1).strip()
                nome_limpo = re.split(r"CPF|CNPJ|Resumo|Assunto|\n", nome_bruto, flags=re.IGNORECASE)[0].strip()
                dados["recorrente"] = _limpar_nome(nome_limpo)

        # Padrão 3: Proprietário:
        if not dados["recorrente"]:
            rec_match = re.search(r"Proprietário:\s*([A-ZÀ-Ü\s\.]+)", texto_completo, re.IGNORECASE)
            if rec_match:
                nome_bruto = rec_match.group(1).strip()
                nome_limpo = re.split(r"CPF|CNPJ|Resumo|Assunto|\n", nome_bruto, flags=re.IGNORECASE)[0].strip()
                dados["recorrente"] = _limpar_nome(nome_limpo)

        # 5. CPF
        dados["cpf"] = _extrair_cpf(texto_completo)

        # 6. CNPJ
        dados["cnpj"] = _extrair_cnpj(texto_completo)

        # 7. Valor da multa
        dados["valor_multa"] = _extrair_valor_multa(texto_completo)

        # 8. Pontos na CNH
        dados["pontos_cnh"] = _extrair_pontos(texto_completo)

        # 9. Artigo do CTB
        dados["artigo_ctb"] = _extrair_artigo_ctb(texto_completo)

        # 10. Veículo (marca/modelo/cor)
        dados["veiculo_completo"] = _extrair_veiculo2(texto_completo)

        return dados, texto_completo

    except FileNotFoundError:
        return None, ""
    except Exception as e:
        print(f"ERRO ao extrair dados do PDF: {e}")
        return None, ""
