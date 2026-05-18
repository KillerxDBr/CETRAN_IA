import os
import datetime as dt
import locale as lc
from pprint import pprint

import streamlit as st

from extrair_pdf import extrair_dados_detran_pdf
from gerar_ia_parecer import mapear_e_analisar_processo_ia
from gerar_parecer import gerar_documento_parecer

lc.setlocale(lc.LC_CTYPE, "")
lc.setlocale(lc.LC_COLLATE, "")
lc.setlocale(lc.LC_TIME, "")

st.write(f"Locale: {lc.setlocale(lc.LC_ALL, None)}")

st.set_page_config(layout="wide", page_title="CETRAN-MT", page_icon="⚖️")

# ========== ESTILO CUSTOMIZADO ==========
# st.markdown(
#     """
# <style>
#     .stTabs [data-baseweb="tab-list"] { gap: 8px; }
#     .stTabs [data-baseweb="tab"] { padding: 10px 20px; border-radius: 8px 8px 0 0; }
#     .stMetric { background: #f0f2f6; padding: 15px; border-radius: 10px; }
#     div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
#     .success-box { padding: 20px; background: #d4edda; border-radius: 10px; border-left: 5px solid #28a745; }
#     .warning-box { padding: 20px; background: #fff3cd; border-radius: 10px; border-left: 5px solid #ffc107; }
# </style>
# """,
#     unsafe_allow_html=True,
# )

# ========== CABEÇALHO ==========
st.title("⚖️ Sistema de Pareceres - CETRAN-MT")
st.caption("Sistema de análise e geração de pareceres para recursos de trânsito")

# ========== INICIALIZAÇÃO DE SESSION STATE ==========
defaults = {
    "nome_arquivo_atual": None,
    "ia_data": None,
    "caminho_gerado": None,
    "texto_bruto": None,
    "basic_data": None,
    "historico": [],
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ========== UPLOAD DE ARQUIVO ==========
st.header("📄 Upload do Processo Digital")
arquivo_pdf = st.file_uploader("Arraste e solte ou selecione o arquivo PDF do processo", type=["pdf"], help="Formatos aceitos: PDF")

if arquivo_pdf:
    # Reset se arquivo mudou
    if st.session_state.nome_arquivo_atual != arquivo_pdf.name:
        st.session_state.nome_arquivo_atual = arquivo_pdf.name
        for key in ["ia_data", "caminho_gerado", "texto_bruto", "basic_data"]:
            st.session_state[key] = None
        st.rerun()

    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("📎 Arquivo", arquivo_pdf.name)
    with col_info2:
        if arquivo_pdf.size > (1024 * 1024):
            metrica = "MB"
            tamanho = round(arquivo_pdf.size / (1024 * 1024), 1)
        else:
            metrica = "KB"
            tamanho = round(arquivo_pdf.size / 1024, 1)
        st.metric("💾 Tamanho", f"{tamanho} {metrica}")
    with col_info3:
        st.metric("🕐 Data Upload", dt.datetime.now().strftime("%d/%m/%Y %H:%M"))

    st.divider()

    # ========== EXTRAÇÃO DE DADOS ==========
    if st.session_state.basic_data is None:
        with st.spinner("🔍 Extraindo dados do PDF..."):
            basic, texto_bruto = extrair_dados_detran_pdf(arquivo_pdf)
            st.session_state.basic_data = basic
            st.session_state.texto_bruto = texto_bruto

    basic = st.session_state.basic_data
    texto_bruto = st.session_state.texto_bruto

    decadencia_options = [
        "Escolha uma Decadencia",
        "Notificação da Autuação dentro do prazo",
        "Notificação da Autuação fora do prazo",
        "Notificação da Penalidade dentro do prazo sem defesa de autuação",
        "Notificação da Penalidade dentro do prazo com defesa de autuação",
        "Notificação da Penalidade fora do prazo sem defesa de autuação",
        "Notificação da Penalidade fora do prazo com defesa de autuação",
    ]

    prescricao_options = [
        "Escolha uma Prescrição",
        "Não ocorrência de prescrição punitiva ou intercorrente",
        "Ocorrência de prescrição punitiva de 05 anos",
        "Ocorrência de prescrição intercorrente de 02 anos do CTB no âmbito da JARI",
        "Ocorrência de prescrição intercorrente de 02 anos do CTB no âmbito do CETRAN",
    ]

    voto_options = [
        "Escolha um Voto",
        "Intempestividade",
        "Ilegitimidade",
        "Falta de assinatura válida",
        "Pedido incompatível com a situação fática",
        "Pedido não cumpre requisitos legais (um recurso para mais de uma autuação)",
        "Cancelamento da autuação por decadência da expedição da Notificação da Autuação",
        "Cancelamento da autuação por decadência da expedição da Notificação da Penalidade",
        "Não conhecimento (Pedido de reconsideração)",
        "Deferimento do pedido por supressão de instância de julgamento",
        "Indeferimento (com mérito)",
        "Deferimento (com mérito)",
    ]

    if basic:
        # ========== ANÁLISE COM IA ==========
        if st.session_state.ia_data is None:
            with st.spinner("🧠 Analisando documento com IA (Ollama)..."):
                st.session_state.ia_data = mapear_e_analisar_processo_ia(texto_bruto)
                st.rerun()

        ia = st.session_state.ia_data

        # ========== TABS ==========
        tab_dados, tab_detalhes, tab_documento = st.tabs(["📋 Dados do Processo", "🔍 Texto Extraído", "📝 Gerar Documento"])

        with tab_dados:
            st.subheader("Informações Principais")

            # Campos principais em grid
            col1, col2, col3 = st.columns(3)
            with col1:
                processo = st.text_input(
                    "Número do Processo", value=basic.get("processo") or "", placeholder="DETRAN-PRO-2025/XXXXX", help="Processo SIGADOC do DETRAN"
                )
                ait = st.text_input("AIT", value=basic.get("ait_numero") or "", placeholder="F433623812")
                placa = st.text_input("Placa do Veículo", value=basic.get("placa") or "", placeholder="AAA0000")
            with col2:
                recorrente = st.text_input("Nome do Recorrente", value=basic.get("recorrente") or ia.get("recorrente", ""), placeholder="Nome completo")
                jari = st.text_input("JARI de Origem", value=ia.get("jari_origem") or "", placeholder="JARI Municipal / DETRAN")
                legitimidade = st.text_input("Legitimidade", value=ia.get("legitimidade") or "", placeholder="Proprietário / Condutor")
            with col3:
                veiculo = st.text_input(
                    "Veículo (Marca/Modelo/Cor)", value=basic.get("veiculo_completo") or ia.get("veiculo_completo") or "", placeholder="Fiat Mobi / Prata"
                )
                local_hora = st.text_input(
                    "Local e Hora da Infração", value=f"{ia.get("local_infracao") or ""} - {ia.get("data_hora") or ""}", placeholder="Av. Principal, 00 - Cidade, 01/01/2025 00:00"
                )
                tipificacao = st.text_input(
                    "Tipificação (Artigo CTB)", value=ia.get("tipificacao") or "", placeholder="Art. 218 do CTB - Excesso de velocidade"
                )
            col1, col2, col3 = st.columns(3)

            with col1:
                data_autuacao = st.text_input("Data De Autuaçao", value=ia.get("data_autuacao", "") or "01/01/2024")
            with col2:
                data_notificacao = st.text_input("Data De Notificação", value=ia.get("data_notificacao", "") or "01/01/2024")
            with col3:
                data_lavratura = st.text_input("Data De Lavratura", value=ia.get("data_lavratura", "") or "01/01/2024")
            # Validação visual
            st.divider()
            st.subheader("⚠️ Validação dos Dados")

            campos_obrigatorios = {
                "Processo": processo,
                "Recorrente": recorrente,
                "AIT": ait,
                "Placa": placa,
            }

            cols_check = st.columns(len(campos_obrigatorios))
            all_valid = True
            for idx, (nome, valor) in enumerate(campos_obrigatorios.items()):
                with cols_check[idx]:
                    if valor and valor.strip():
                        st.success(f"✅ {nome}")
                    else:
                        st.error(f"❌ {nome}")
                        all_valid = False

            if not all_valid:
                st.markdown(
                    '<div class="warning-box">Preencha todos os campos obrigatórios (em vermelho) antes de gerar o documento.</div>', unsafe_allow_html=True
                )

        with tab_detalhes:
            st.subheader("📄 Texto Ext do PDF")
            with st.expander("Ver texto completo extraído", expanded=False):
                if texto_bruto:
                    st.text_area("Conteúdo do PDF", value=texto_bruto[:15000] + ("..." if len(texto_bruto) > 15000 else ""), height=400, disabled=True)
                    st.caption(f"Total: {len(texto_bruto)} caracteres")
                else:
                    st.info("Nenhum texto extraído.")

            if ia:
                st.divider()
                st.subheader("🧠 Dados Analisados pela IA")
                col_ia1, col_ia2 = st.columns(2)
                with col_ia1:
                    st.json(ia)
                with col_ia2:
                    st.info("💡 Os campos acima foram preenchidos automaticamente pela IA. Você pode editá-los na aba 'Dados do Processo'.")

        with tab_documento:
            st.subheader("⚖️ Configuração do Parecer")

            col1, col2, col3 = st.columns(3)
            with col1:
                ano_parecer = st.text_input("Ano do Parecer", value=str(
                    dt.datetime.now().year), disabled=True)
                hip_decadencia = st.selectbox(
                    "Decadencia",
                    options=decadencia_options,
                )

            with col2:
                voto_final = st.selectbox("Resultado do Voto", options=["INDEFERIMENTO", "DEFERIMENTO", "PARCIALMENTE DEFERIDO"])
                hip_prescricao = st.selectbox(
                    "Prescrição",
                    options=prescricao_options,
                )

            with col3:
                num_parecer = st.text_input(
                    "Número do Parecer", placeholder="0001/2025")
                hip_voto = st.selectbox(
                    "Voto",
                    options=voto_options,
                )

            st.divider()

            # Preview do pacote
            st.subheader("📋 Resumo dos Dados para Geração")
            dateFormat = "%d/%m/%Y"
            data_lavratura_dt   = dt.datetime.strptime(data_lavratura, dateFormat)
            data_notificacao_dt = dt.datetime.strptime(data_notificacao, dateFormat)

            pacote_preview = {
                "processo": processo or "-",
                "recorrente": recorrente or "-",
                "ait_numero": ait or "-",
                "placa_veiculo": placa or "-",
                "num_parecer": num_parecer or "-",
                "ano": ano_parecer or "-",
                "jari_origem": jari or "-",
                "veiculo_completo": veiculo or "-",
                "local_hora": local_hora or "-",
                "tipificacao": tipificacao or "-",
                "legitimidade": legitimidade or "-",
                "voto_final": voto_final or "-",
                "decadencia_hip": decadencia_options.index(hip_decadencia) or 0,
                "prescricao_hip": prescricao_options.index(hip_prescricao) or 0,
                "voto_hip": voto_options.index(hip_voto) or 0,
                "data_autuacao": data_autuacao or "-",
                "data_lavratura_ait": data_lavratura or "-",
                "data_notificacao": data_notificacao or "-",
                "dias_autuacao_na": (data_notificacao_dt - data_lavratura_dt).days or "-",
            }
            st.json(pacote_preview)

            st.divider()

            # Botão de geração
            if st.button("🚀 GERAR PARECER", type="primary", disabled=not all_valid):
                print(f"{data_autuacao=}")
                print(f"{data_lavratura=}")
                print(f"{data_notificacao=}")

                dateFormat = "%d/%m/%Y"

                data_autuacao_dt = dt.datetime.strptime(data_autuacao, dateFormat)
                data_lavratura_dt = dt.datetime.strptime(data_lavratura, dateFormat)
                data_notificacao_dt = dt.datetime.strptime(data_notificacao, dateFormat)

                pacote = {
                    "processo": processo,
                    "recorrente": recorrente,
                    "ait_numero": ait,
                    "placa_veiculo": placa,
                    "num_parecer": num_parecer,
                    "ano": ano_parecer,
                    "jari_origem": jari,
                    "veiculo_completo": veiculo,
                    "local_hora": local_hora,
                    "tipificacao": tipificacao,
                    "legitimidade": legitimidade,
                    "voto_final": voto_final,
                    "decadencia_hip": decadencia_options.index(hip_decadencia) or 0,
                    "prescricao_hip": prescricao_options.index(hip_prescricao) or 0,
                    "voto_hip": voto_options.index(hip_voto) or 0,
                    "data_autuacao": data_autuacao,
                    "data_lavratura_ait": data_lavratura,
                    "data_notificacao": data_notificacao,
                    "dias_autuacao_na": (data_notificacao_dt - data_lavratura_dt).days,
                }

                pprint(pacote)

                with st.spinner("📝 Gerando documento Word..."):
                    caminho = gerar_documento_parecer(pacote)

                if caminho:
                    st.session_state.caminho_gerado = caminho
                    st.session_state.historico.append(
                        {
                            "arquivo": arquivo_pdf.name,
                            "data": dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "caminho": caminho,
                            "AIT": ait,
                        }
                    )
                    st.rerun()

            # Download do documento gerado
            if st.session_state.caminho_gerado:
                st.divider()
                st.markdown('<div class="success-box">✅ Documento gerado com sucesso!</div>', unsafe_allow_html=True)

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    with open(st.session_state.caminho_gerado, "rb") as f:
                        st.download_button("📥 BAIXAR PARECER (DOCX)", f, file_name=os.path.basename(st.session_state.caminho_gerado), type="primary")
                with col_dl2:
                    if st.button("🗑️ Limpar e Processar Novo"):
                        for key in list(st.session_state.keys()):
                            if key != "historico":
                                st.session_state[key] = None
                        st.rerun()

    else:
        st.error("❌ Não foi possível extrair dados do PDF. Verifique se o arquivo é um processo válido.")

# ========== HISTÓRICO ==========
if st.session_state.historico:
    st.divider()
    st.header("📚 Histórico de Documentos Gerados")
    for item in reversed(st.session_state.historico[-5:]):
        col_h1, col_h2, col_h3 = st.columns([3, 2, 1])
        with col_h1:
            st.text(f"📄 {item['AIT']}")
        with col_h2:
            st.caption(item["data"])
        with col_h3:
            with open(item["caminho"], "rb") as f:
                st.download_button("📥", f, file_name=os.path.basename(item["caminho"]), key=f"dl_{item['data'].replace(':', '')}")
