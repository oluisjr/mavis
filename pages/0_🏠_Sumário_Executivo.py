"""Painel executivo com indicadores heurísticos transparentes."""
import streamlit as st
from app import analysis, config, data_loader, session_manager, ui_components

st.set_page_config(page_title="MAVIS | Visão geral", page_icon=config.FAVICON_PATH, layout="wide")
session_manager.check_authentication()
ui_components.hide_main_page_nav_and_footer()
ui_components.render_mavis_header()
df = data_loader.carregar_dados_iniciais()
ui_components.render_sidebar(df, "anual")

st.subheader("Visão geral do processo")
filtros = st.session_state.filtros_aplicados
series, avisos = data_loader.obter_visoes_filtradas(filtros)
ui_components.mensagens_de_origem(avisos)
if filtros.get("receita_fmt") == "Todas":
    st.info("Selecione uma receita específica para comparar tendências e índices de desvio.")
    st.stop()

diario = series["diario"]
mensal = series["mensal"]
base = diario if not diario.empty else mensal
st.caption(
    "Resultados descritivos baseados nos registros existentes. "
    "Índice de desvio não é probabilidade de falha nem indicador certificado de saúde do equipamento."
)
if base.empty:
    st.warning("Não há dados para os filtros selecionados.")
    st.stop()

disponiveis = [s for s in config.NOMES_SENSORES if s in base and s not in config.SENSORES_INDISPONIVEIS]
if not disponiveis:
    st.warning("Não há sensores habilitados com dados suficientes.")
    st.stop()

colunas = st.columns(min(4, len(disponiveis)))
indices = {}
for i, sensor in enumerate(disponiveis):
    indice = analysis.calcular_indice_desvio(base, sensor)
    indices[sensor] = indice
    with colunas[i % len(colunas)]:
        st.metric(config.NOMES_SENSORES[sensor], ui_components.formatar_indice(indice))
        st.caption(analysis.detectar_anomalia(base, sensor))

for sensor in sorted(config.SENSORES_INDISPONIVEIS):
    if sensor in config.NOMES_SENSORES:
        st.warning(f"{config.NOMES_SENSORES[sensor]}: indisponível por configuração operacional. "
                   "Reabilitar apenas após confirmação técnica.")

validos = [(s, ind) for s, ind in indices.items() if ind is not None]
if validos:
    critico, maior = max(validos, key=lambda item: item[1])
    st.divider()
    st.subheader("Maior desvio estatístico observado")
    st.metric(config.NOMES_SENSORES[critico], f"{maior:.1f}/100")
    st.write(analysis.analisar_tendencia(base, critico))
    st.markdown("**Hipóteses técnicas para investigação (não é diagnóstico de causa raiz):**")
    causas = analysis.analisar_causa_raiz(critico)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Possíveis mecanismos**")
        for c in causas.get("causas_provaveis", []):
            st.write(c)
    with col2:
        st.markdown("**Verificações sugeridas**")
        for a in causas.get("acoes_recomendadas", []):
            st.write(a)
else:
    st.info("Amostras insuficientes para emitir índice de desvio (mínimo de 8 por sensor).")

st.divider()
st.caption("A saída do MAVIS deve ser confrontada com limites aprovados pela engenharia e com dados de manutenção.")
