from datetime import datetime
from os import abort
from pprint import pprint
import re

import pdfplumber
from extrair_pdf import _extrair_veiculo

teste = {"aee": "HOOOOO", "sla": "skjsakd"}
# for k,v  in teste.items():
#     print(k, v)
# teste_str = f'{'\n'.join([f'{i} -> \"{k}\": \"{v}\",' for i, (k,v) in enumerate(teste.items())])}'
teste_str = f"{'\n'.join([f'    "{k}": "{v}"{'' if i == len(teste) else ','}' for i, (k, v) in enumerate(teste.items(), 1)])}"
print(teste_str)
exit(0)


def extrair_veiculo(texto: str):
    for line in texto.split("\n"):
        if line.startswith("2.2 - MARCA/MODELO:"):
            line = line.removeprefix("2.2 - MARCA/MODELO:").split("-")[0].strip()
            return line
    return ""
    return _extrair_veiculo(texto)


regex_data = re.compile(r"(0[1-9]|[12][0-9]|3[01])(\/|-)(0[1-9]|1[1,2])(\/|-)(19|20)\d{2}")


def extrair_data(texto: str):
    rst = []
    # for line in texto.split("\n"):
    #     l = line.lower()
    #     # if l.find("/20") != -1:
    #     if l.find("postagem") != -1:
    #         rst.append(line)
    re_finds = regex_data.findall(texto)
    pprint(re_finds, indent=4)
    return rst


files = [
    # "DETRANPRO202418432V01.pdf",
    # "DETRANPRO202422751V01.pdf",
    # "DETRANPRO202501016V01.pdf",
    "temp_analise.pdf",
]

for f in files:
    texto_completo = []

    try:
        with pdfplumber.open(f) as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text() or ""
                # if texto_pagina:
                texto_completo.append(texto_pagina.strip())
    except Exception as e:
        print("ERROR: {e}")

    print(f"{f}[{len(texto_completo)}]:")
    for x in texto_completo:
        print("  ", x)
    # pprint(texto_completo, indent=4)
    continue

    # print(f"{f}: {_extrair_veiculo(texto_completo) = }")
    # print(f"{f}: {extrair_veiculo(texto_completo) = }")
    # print(_extrair_veiculo(texto_completo))
    print(f"{f}:")
    rst = extrair_data(texto_completo)
    if len(rst):
        pprint(rst, indent=4)
        str_rst: str = rst[0]
        if len(rst) > 1:
            abort()

        print(f"{str_rst = }")

        splited = str_rst.strip().split(":")
        print(f"{len(splited) = }")
        if len(splited) > 1:
            hasDigits = False
            for x in splited[0]:
                hasDigits = x.isdigit()
                if hasDigits:
                    # sys.exit("hasDigits not implemented")
                    pass
            newStr = str_rst.removeprefix(f"{splited[0]}:").strip()
            print(f"{newStr = }")
            data_autuacao = datetime.strptime(newStr, "%d/%m/%Y %H:%M:%S")
            print(data_autuacao)
    else:
        print("Data Nao encontrada")
