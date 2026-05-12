import pdfplumber
from extrair_pdf import _extrair_veiculo
import re


def extrair_veiculo(texto: str):
    for line in texto.split("\n"):
        if line.startswith("2.2 - MARCA/MODELO:"):
            line = line.removeprefix("2.2 - MARCA/MODELO:").split("-")[0].strip()
            return line
    return ""
    return _extrair_veiculo(texto)


files = [
    "DETRANPRO202418432V01.pdf",
    "DETRANPRO202422751V01.pdf",
    "DETRANPRO202501016V01.pdf",
    "temp_analise.pdf",
]

for f in files:
    texto_completo = ""

    try:
        with pdfplumber.open(f) as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text() or ""
                texto_completo += texto_pagina + "\n"
    except Exception as e:
        print("ERROR: {e}")

    print(f"{f}: {_extrair_veiculo(texto_completo) = }")
    print(f"{f}: {extrair_veiculo(texto_completo) = }")
    # print(_extrair_veiculo(texto_completo))
