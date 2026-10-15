"""Visualização diária dos sensores usando a mesma base filtrada dos índices."""
import streamlit as st
from app import analysis, config, data_loader, session_manager, ui_components

st.set_page_config(page_title="MAVIS | Diário", page_icon=config.FAVICON_PATH, layout="wide")
session_manager.check_authentication()
ui_components.hide_main_page_nav_and_footer()
ui_components.render_mavis_header()
registros = data_loader.carregar_dados_iniciais()
ui_components.render_sidebar(registros, "diaria")
st.subheader("Análise diária")

filtros = st.session_state.filtros_aplicados
series, avisos = data_loader.obter_visoes_filtradas(filtros)
ui_components.mensagens_de_origem(avisos)
dados = series["diario"]
if dados.empty:
    st.warning("Não há registros diários para os filtros selecionados.")
    st.stop()
if filtros.get("receita_fmt") == "Todas":
    st.warning("Dados combinados de diferentes receitas: gráficos descritivos, sem diagnóstico de anomalia.")

st.caption("Os indicadores usam as mesmas médias diárias filtradas dos gráficos. São sinais de triagem: podem ocultar variações entre soldas ou dentro delas. Para investigar, abra Análise por Solda.")
for sensor, nome in config.NOMES_SENSORES.items():
    if sensor in config.SENSORES_INDISPONIVEIS:
        st.info(f"{nome}: medição atualmente indisponível por configuração operacional.")
        continue
    if sensor not in dados or dados[sensor].notna().sum() == 0:
        st.info(f"{nome}: sem leituras disponíveis no período.")
        continue
    st.divider()
    st.markdown(f"#### {nome}")
    st.line_chart(dados.set_index("DATA")[sensor])
    if filtros.get("receita_fmt") == "Todas":
        continue
    st.write(analysis.detectar_anomalia(dados, sensor))
    st.write(analysis.analisar_tendencia(dados, sensor))
    indice = analysis.calcular_indice_desvio(dados, sensor)
    if indice is not None and indice >= 40:
        with st.expander("Hipóteses de investigação e inspeções"):
            conhecimento = analysis.analisar_causa_raiz(sensor)
            st.caption("Hipóteses genéricas, não confirmadas por modelo de diagnóstico.")
            for causa in conhecimento.get("causas_provaveis", []):
                st.write(causa)
            st.markdown("**Ações sugeridas**")
            for acao in conhecimento.get("acoes_recomendadas", []):
                st.write(acao)
