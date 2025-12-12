import streamlit as st
import pandas as pd
from app import config, analysis, ui_components, data_loader, session_manager
import streamlit.components.v1 as components
from pyecharts import options as opts
from pyecharts.charts import HeatMap

# ============================================================
# VERIFICA LOGIN
# ============================================================
if not st.session_state.get('authenticated', False):
    st.error("Acesso negado. Por favor, faça o login na aba Início.")
    st.stop()
    
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
    page_title = "MAVIS - Análise Mensal"

st.set_page_config(
    page_title=page_title,
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=favicon
)

ui_components.hide_main_page_nav_and_footer()

df_total_completo = data_loader.carregar_dados_iniciais()
ui_components.render_sidebar(df_total_completo, page_name='mensal')

image, title, blank = st.columns([1, 4, 1], vertical_alignment="center")
with image: st.image(config.LOGO_PATH, width=80)
with title: ui_components.render_mavis_header(theme=st.session_state.get('theme', 'light'))

st.subheader("Análise Mensal dos Sensores")

# --- Leitura dos Dados e Aplicação dos Filtros ---
filtros = st.session_state.get('filtros_aplicados', {})
receita_str = filtros.get('receita_fmt', '1')
(df_total, df_diario, df_semanal, df_mensal, df_anual), messages = data_loader.carregar_dados_por_receita(receita_str)
riscos_mes = st.session_state.get('riscos_mes', {})

if df_mensal.empty:
    st.warning("Não há dados mensais para a receita selecionada.")
    st.stop()

# Aplica filtros de período da sidebar
df_mensal_filtrado = df_mensal.copy()
df_semanal_filtrado = df_semanal.copy()

df_mensal_filtrado['MES'] = pd.to_datetime(df_mensal_filtrado['MES'], errors='coerce')

if filtros.get('anos'):
    df_mensal_filtrado = df_mensal_filtrado[df_mensal_filtrado['MES'].dt.year.isin(filtros['anos'])]
    df_semanal_filtrado = df_semanal_filtrado[df_semanal_filtrado['SEMANA'].dt.year.isin(filtros['anos'])]
if filtros.get('meses'):
    df_mensal_filtrado = df_mensal_filtrado[df_mensal_filtrado['MES'].dt.month.isin(filtros['meses'])]
    df_semanal_filtrado = df_semanal_filtrado[df_semanal_filtrado['SEMANA'].dt.month.isin(filtros['meses'])]

# --- Renderização do Conteúdo ---
if df_mensal_filtrado.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
else:
    for sensor in config.CORES.keys():
        
        st.markdown("---")
        
        # --- Início da Lógica do Antigo `layout_sensor` ---
        if sensor == "TEMPERATURA":
            st.subheader(f":red[{config.NOMES_SENSORES.get(sensor, sensor)}]", divider="red")
        else:
            st.subheader(config.NOMES_SENSORES.get(sensor, sensor))
            st.markdown(analysis.detectar_anomalia(df_mensal_filtrado, sensor=sensor))

        col_linha, col_direita = st.columns([4, 3])

        with col_linha:
            
            if sensor == "TEMPERATURA":
                st.markdown("### ⚠️ :gray-background[Sensor inoperante, impossível analisar!] ⚠️")
            else:
                st.write("Gráfico de Linha")
                st.line_chart(df_mensal_filtrado.set_index('MES')[sensor])
                with st.expander("Ver análise detalhada da IA"):
                    st.caption(analysis.analisar_tendencia(df_mensal_filtrado, sensor, sensor=sensor))


        with col_direita:
            if sensor == "TEMPERATURA":
                #st.markdown("### ⚠️ :gray-background[Sensor inoperante, impossível analisar!] ⚠️") # Pirômetro quebrado
                continue
            else:
                st.write("Gráfico de Barra")
                st.bar_chart(df_mensal_filtrado.set_index('MES')[sensor], height=200, use_container_width=True)

                st.write("Gráfico de Área")
                st.area_chart(df_mensal_filtrado.set_index('MES')[sensor], color="#1f77b4AA", height=100, use_container_width=True)

            # if sensor == "TEMPERATURA" and not df_semanal_filtrado.empty:
            #     st.markdown("<br>", unsafe_allow_html=True)
            #     st.write("Mapa de Calor da Temperatura (Semanal x Mensal)")
                
            #     df_semanal_filtrado['SEMANA_NUM'] = df_semanal_filtrado['SEMANA'].dt.isocalendar().week
            #     heatmap_data = []
            #     semanas = sorted(df_semanal_filtrado['SEMANA_NUM'].dropna().unique().tolist())
            #     meses = df_semanal_filtrado['SEMANA'].dt.to_period("M").astype(str).unique().tolist()

            #     for i, semana_num in enumerate(semanas):
            #         for j, mes_str in enumerate(meses):
            #             media_temp = df_semanal_filtrado[
            #                 (df_semanal_filtrado['SEMANA_NUM'] == semana_num) &
            #                 (df_semanal_filtrado['SEMANA'].dt.to_period("M").astype(str) == mes_str)
            #             ]['TEMPERATURA'].mean()
            #             if pd.notna(media_temp):
            #                 heatmap_data.append([j, i, round(media_temp)])

            #     if heatmap_data:
            #         valores = [p[2] for p in heatmap_data]
            #         heatmap = (
            #             HeatMap()
            #             .add_xaxis(meses)
            #             .add_yaxis("Semanas", semanas, heatmap_data)
            #             .set_global_opts(
            #                 title_opts=opts.TitleOpts(title="Temperatura Média (ºC)"),
            #                 visualmap_opts=opts.VisualMapOpts(min_=min(valores), max_=max(valores)),
            #                 xaxis_opts=opts.AxisOpts(type_="category", name="Mês"),
            #                 yaxis_opts=opts.AxisOpts(type_="category", name="Semana")
            #             )
            #         )
            #         components.html(heatmap.render_embed(), height=550, width=1400, scrolling=True)
            #     else:
            #         st.warning("Não há dados semanais suficientes para gerar o mapa de calor para este período.")









