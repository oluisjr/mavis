import streamlit as st
import pandas as pd
from app import config, analysis, ui_components, data_loader
import streamlit.components.v1 as components


# --- Configurações, Sidebar e Cabeçalho ---
if 'error_occurred' not in st.session_state:
    st.session_state.error_occurred = False

if st.session_state.error_occurred:
    favicon = config.FAVICON_ERRO_PATH
    logo = config.LOGO_ERRO_PATH
    page_title = "MAVIS - Erro"
else:
    favicon = config.FAVICON_PATH
    logo = config.LOGO_PATH
    page_title = "MAVIS - Análise Diária"

st.set_page_config(
    page_title=page_title,
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=favicon
)

ui_components.hide_streamlit_elements()

df_total_completo = data_loader.carregar_dados_iniciais()
# A página chama a sua própria sidebar, passando o identificador 'diaria'
ui_components.render_sidebar(df_total_completo, page_name='diaria')

image, title, blank = st.columns([1, 4, 1], vertical_alignment="center")
with image: st.image(config.LOGO_PATH, width=80)
with title: ui_components.render_mavis_header(theme=st.session_state.get('theme', 'light'))

st.subheader("Análise Diária dos Sensores")

# --- Leitura dos Dados e Aplicação dos Filtros ---
filtros = st.session_state.get('filtros_aplicados', {})
receita_str = filtros.get('receita_fmt', '123')
(df_total, df_diario, df_semanal, df_mensal, df_anual), messages = data_loader.carregar_dados_por_receita(receita_str)

# Você precisará calcular os riscos aqui se a página os usar
riscos_dia = {}
if not df_diario.empty:
    riscos_dia = {s: analysis.simular_risco_por_regras(df_diario, s) for s in config.NOMES_SENSORES.keys()}

if df_diario.empty:
    st.warning("Não há dados diários para a receita selecionada.")
    st.stop()

# Aplica os filtros da sidebar
df_final = df_diario.copy()
if filtros.get('anos'): df_final = df_final[df_final['DATA'].dt.year.isin(filtros['anos'])]
if filtros.get('meses'): df_final = df_final[df_final['DATA'].dt.month.isin(filtros['meses'])]
if filtros.get('dias'): df_final = df_final[df_final['DATA'].dt.day.isin(filtros['dias'])]

# --- Renderização do Conteúdo ---
if df_final.empty:
    st.info("Nenhum dado encontrado para os filtros de período selecionados.")
else:
    # O seu layout original para exibir os gráficos diários
    sensores = list(config.CORES.keys())
    col1, col2 = st.columns(2)
    with col1:
        for sensor in sensores[:2]:
            col_nome, col_liquid = st.columns([5, 0.8])
            with col_nome:
                st.write(f"## {config.NOMES_SENSORES[sensor]}")
            with col_liquid:
                riscos_semana = {}
                if not df_semanal.empty:
                    riscos_semana = {s: analysis.simular_risco_por_regras(df_semanal, s) for s in config.NOMES_SENSORES.keys()}

                riscos_mes = {}
                if not df_mensal.empty:
                    riscos_mes = {s: analysis.simular_risco_por_regras(df_mensal, s) for s in config.NOMES_SENSORES.keys()}
                    
                riscos_para_analise = riscos_semana if riscos_semana else riscos_mes

                risco = riscos_para_analise.get(sensor, 0)
                score = analysis.calcular_health_score(risco)
                liquid_html_raw =ui_components.render_mini_liquid_chart(score)
                centered_liquid_html = f"""<div style="display: flex; justify-content: center; align-items: center; height: 60px; width: 100%;">{liquid_html_raw}</div>"""
                components.html(centered_liquid_html, height=80)
                
            st.markdown(analysis.detectar_anomalia(df_final, sensor))
            st.line_chart(df_final.set_index('DATA')[sensor])
                
            with st.expander("Ver análise detalhada da IA"):
                st.caption(analysis.analisar_tendencia(df_final, sensor, sensor=sensor))
                st.markdown("---")
                    
                if riscos_dia and sensor in riscos_dia:
                    st.write("**Potencial de falha iminente (%)**")
                    risco_valor = riscos_dia[sensor]
                    if risco_valor > 75: st.error(f"**Risco Elevado:** {risco_valor:.1f}%")
                    elif risco_valor > 50: st.warning(f"**Atenção:** {risco_valor:.1f}%")
                    elif risco_valor > 20: st.info(f"**Risco Moderado:** {risco_valor:.1f}%")
                    else: st.success(f"**Risco Baixo:** {risco_valor:.1f}%")
                else:
                    st.info("Simulação de risco indisponível.")
                if sensor in riscos_dia:
                    status_sensor = analysis.detectar_anomalia(df_final, sensor)
                    if "Normal" not in status_sensor:
                        st.markdown("---")
                        st.write("**Análise de Causa Raiz:**")
                        rca_sensor = analysis.analisar_causa_raiz(sensor)
                        st.caption(f"**Causas Prováveis:**\n" + '\n'.join(rca_sensor['causas_provaveis']))
                        st.caption(f"**Ações Recomendadas:**\n" + '\n'.join(rca_sensor['acoes_recomendadas']))
                    else:
                        st.info("Tudo normal por aqui...")

    with col2:
        for sensor in sensores[2:4]:
            col_nome, col_liquid = st.columns([5, 0.8])
            with col_nome:
                st.write(f"## {config.NOMES_SENSORES[sensor]}")
            with col_liquid:
                riscos_semana = {}
                if not df_semanal.empty:
                    riscos_semana = {s: analysis.simular_risco_por_regras(df_semanal, s) for s in config.NOMES_SENSORES.keys()}

                riscos_mes = {}
                if not df_mensal.empty:
                    riscos_mes = {s: analysis.simular_risco_por_regras(df_mensal, s) for s in config.NOMES_SENSORES.keys()}
                    
                riscos_para_analise = riscos_semana if riscos_semana else riscos_mes

                risco = riscos_dia.get(sensor, 100)
                score = analysis.calcular_health_score(risco)
                liquid_html_raw =ui_components.render_mini_liquid_chart(score)
                centered_liquid_html = f"""<div style="display: flex; justify-content: center; align-items: center; height: 60px; width: 100%;">{liquid_html_raw}</div>"""
                components.html(centered_liquid_html, height=80)
                
            st.markdown(analysis.detectar_anomalia(df_final, sensor))
            st.line_chart(df_final.set_index('DATA')[sensor])

            with st.expander("Ver análise detalhada da IA"):
                st.caption(analysis.analisar_tendencia(df_final, sensor, sensor=sensor))
                st.markdown("---")
                    
                if riscos_dia and sensor in riscos_dia:
                    st.write("**Potencial de falha iminente (%)**")
                    risco_valor = riscos_dia[sensor]
                    if risco_valor > 75: st.error(f"**Risco Elevado:** {risco_valor:.1f}%")
                    elif risco_valor > 50: st.warning(f"**Atenção:** {risco_valor:.1f}%")
                    elif risco_valor > 20: st.info(f"**Risco Moderado:** {risco_valor:.1f}%")
                    else: st.success(f"**Risco Baixo:** {risco_valor:.1f}%")
                else:
                    st.info("Simulação de risco indisponível.")
                if sensor in riscos_dia:
                    status_sensor = analysis.detectar_anomalia(df_final, sensor)
                    if "Normal" not in status_sensor:
                        st.markdown("---")
                        st.write("**Análise de Causa Raiz:**")
                        rca_sensor = analysis.analisar_causa_raiz(sensor)
                        st.caption(f"**Causas Prováveis:**\n" + '\n'.join(rca_sensor['causas_provaveis']))
                        st.caption(f"**Ações Recomendadas:**\n" + '\n'.join(rca_sensor['acoes_recomendadas']))
                    else:
                        st.info("Tudo normal por aqui...")

    sensor_atual = sensores[4]
    st.write(f"## :red[{config.NOMES_SENSORES[sensor_atual]}]")
    for sensor in sensores[4:]:
        st.markdown("### ⚠️ :gray-background[Sensor inoperante, impossível analisar!] ⚠️") # Pirômetro quebrado
        # st.markdown(analysis.detectar_anomalia(df_final, sensor))
        # st.line_chart(df_final.set_index('DATA')[sensor])

        # with st.expander("Ver análise detalhada da IA"):
        #     st.caption(analysis.analisar_tendencia(df_final, sensor, sensor=sensor))
        #     st.markdown("---")
                
        #     if riscos_dia and sensor in riscos_dia:
        #         st.write("**Potencial de falha iminente (%)**")
        #         risco_valor = riscos_dia[sensor]
        #         if risco_valor > 75: st.error(f"**Risco Elevado:** {risco_valor:.1f}%")
        #         elif risco_valor > 50: st.warning(f"**Atenção:** {risco_valor:.1f}%")
        #         elif risco_valor > 20: st.info(f"**Risco Moderado:** {risco_valor:.1f}%")
        #         else: st.success(f"**Risco Baixo:** {risco_valor:.1f}%")
        #     else:
        #         st.info("Simulação de risco indisponível.")
        #     if sensor in riscos_dia:
        #         status_sensor = analysis.detectar_anomalia(df_final, sensor)
        #         if "Normal" not in status_sensor:
        #             st.markdown("---")
        #             st.write("**Análise de Causa Raiz:**")
        #             rca_sensor = analysis.analisar_causa_raiz(sensor)
        #             st.caption(f"**Causas Prováveis:**\n" + '\n'.join(rca_sensor['causas_provaveis']))
        #             st.caption(f"**Ações Recomendadas:**\n" + '\n'.join(rca_sensor['acoes_recomendadas']))
        #         else:
        #             st.info("Tudo normal por aqui...")


