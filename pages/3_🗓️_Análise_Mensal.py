"""Comparação mensal por receita e filtros auditáveis."""
import streamlit as st
from app import analysis, config, data_loader, session_manager, ui_components

st.set_page_config(page_title="MAVIS | Mensal", page_icon=config.FAVICON_PATH, layout="wide")
session_manager.check_authentication()
ui_components.hide_main_page_nav_and_footer()
ui_components.render_mavis_header()
registros = data_loader.carregar_dados_iniciais()
ui_components.render_sidebar(registros, "mensal")
st.subheader("Análise mensal")

filtros = st.session_state.filtros_aplicados
series, avisos = data_loader.obter_visoes_filtradas(filtros)
ui_components.mensagens_de_origem(avisos)
dados = series["mensal"]
if dados.empty:
    st.warning("Não há dados mensais para os filtros selecionados.")
    st.stop()
st.caption("Médias por mês; as mudanças observadas não representam necessariamente falhas.")
for sensor, nome in config.NOMES_SENSORES.items():
    st.divider()
    st.markdown(f"#### {nome}")
    if sensor in config.SENSORES_INDISPONIVEIS:
        st.info("Sensor indisponível para análise operacional.")
        continue
    if sensor not in dados or dados[sensor].notna().sum() == 0:
        st.info("Dados indisponíveis para esta variável.")
        continue
    col1, col2 = st.columns([3, 2])
    with col1:
        st.line_chart(dados.set_index("MES")[sensor])
    with col2:
        st.bar_chart(dados.set_index("MES")[sensor])
    if filtros.get("receita_fmt") != "Todas":
        st.write(analysis.analisar_tendencia(dados, sensor))
        st.write(analysis.detectar_anomalia(dados, sensor))
    else:
        st.caption("Selecione uma receita para interpretar variações.")
