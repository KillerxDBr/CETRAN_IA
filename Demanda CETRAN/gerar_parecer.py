import datetime as dt
from pathlib import Path
from docxtpl import DocxTemplate
import os
from pprint import pprint

def validar_campos_obrigatorios(dados):
    """Valida campos obrigatórios para geração do parecer."""
    obrigatorios = ["processo", "recorrente", "ait_numero", "placa_veiculo", "voto_final"]
    faltantes = [campo for campo in obrigatorios if not dados.get(campo) or not dados.get(campo).strip()]
    return faltantes


def gerar_documento_parecer(dados):
    nome_template = "template_parecer.docx"
    caminho_template = os.path.join("templates", nome_template)

    if not os.path.exists(caminho_template):
        print(f"ERRO: Template não encontrado em {caminho_template}")
        return None

    # Validação de campos obrigatórios
    faltantes = validar_campos_obrigatorios(dados)
    if faltantes:
        print(f"ERRO: Campos obrigatórios faltando: {', '.join(faltantes)}")
        return None

    try:
        doc = DocxTemplate(caminho_template)

        defaultDate = dt.datetime.strftime(dt.datetime.fromtimestamp(0), "%d/%m/%Y")

        contexto = {
            "n_processo": dados.get("processo", "").strip(),
            "ait_numero": dados.get("ait_numero", "").strip(),
            "recorrente": dados.get("recorrente", "").strip(),
            "placa_veiculo": dados.get("placa_veiculo", "").strip(),
            "num_parecer": dados.get("num_parecer", "").strip() or "____",
            "ano": dados.get("ano", "").strip() or str(dt.datetime.now().year),
            "jari_origem": dados.get("jari_origem", "").strip(),
            "veiculo_completo": dados.get("veiculo_completo", "").strip(),
            "local_hora": dados.get("local_hora", "").strip(),
            "tipificacao": dados.get("tipificacao", "").strip(),
            "legitimidade": dados.get("legitimidade", "").strip(),
            "analise_admissibilidade": dados.get("analise_admissibilidade", "").strip(),
            "voto_final": dados.get("voto_final", "INDEFERIMENTO").strip(),
            "decadencia_hip": dados.get("decadencia_hip"),
            "prescricao_hip": dados.get("prescricao_hip"),
            "voto_hip": dados.get("voto_hip"),
            "data_postagem_na": dados.get("data_notificacao", defaultDate),
            "dias_autuacao_na": dados.get("dias_autuacao_na", 1),
            "data_lavratura_ait": dados.get("data_lavratura_ait", defaultDate),
            "data_parecer": dt.datetime.now().strftime("%d de %B de %Y"),
        }

        doc.render(contexto)

        os.makedirs("arquivos_gerados", exist_ok=True)
        # Nome do arquivo: Parecer_[AIT].docx
        nome_saida = f"Parecer_{dados.get('ait_numero', 'GERADO').strip()}_{dt.datetime.now().strftime('%d_%m_%Y-%H_%M_%S')}.docx"
        # nome_saida = nome_saida.replace("/", "-").replace("\\", "-")
        caminho_saida = Path("arquivos_gerados") / nome_saida
        # caminho_saida = os.path.join("arquivos_gerados", nome_saida)

        missing = doc.get_undeclared_template_variables()

        print("Faltando:", end="")
        pprint(missing)

        doc.save(caminho_saida)
        return str(caminho_saida.resolve())

    except Exception as e:
        print(f"ERRO ao renderizar Word: {e}")
        return None
