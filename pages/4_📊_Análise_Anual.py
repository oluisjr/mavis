import streamlit as st
import pandas as pd
from app import config, analysis, ui_components, data_loader, session_manager

session_manager.initialize_session_state()

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
    page_title = "MAVIS - Análise Anual"

st.set_page_config(
    page_title=page_title,
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=favicon
)

ui_components.hide_main_page_nav_and_footer()

df_total_completo = data_loader.carregar_dados_iniciais()
ui_components.render_sidebar(df_total_completo, page_name='anual')

image, title, blank = st.columns([1, 4, 1], vertical_alignment="center")
with image: st.image(config.LOGO_PATH, width=80)
with title: ui_components.render_mavis_header(theme=st.session_state.get('theme', 'light'))

st.subheader("Análise Anual dos Sensores")

# --- Leitura dos Dados e Aplicação dos Filtros ---
filtros = st.session_state.get('filtros_aplicados', {})
receita_str = filtros.get('receita_fmt', '123')
(df_total, df_diario, df_semanal, df_mensal, df_anual), messages = data_loader.carregar_dados_por_receita(receita_str)

if df_anual.empty:
    st.warning("Não há dados anuais para a receita selecionada.")
    st.stop()

# Aplica filtros de período da sidebar
df_anual_filtrado = df_anual.copy()
if filtros.get('anos'):
    df_anual_filtrado = df_anual_filtrado[df_anual_filtrado['ANO'].dt.year.isin(filtros['anos'])]

# --- Renderização do Conteúdo ---
if df_anual_filtrado.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
else:
    for sensor in config.CORES.keys():
        st.markdown("---")
        if sensor == "TEMPERATURA":
            st.subheader(config.NOMES_SENSORES.get(sensor, sensor))
            
            # HTML e CSS para o cartão de aviso e o popup
            popup_html = """
                <style>
                #card-temperatura {
                    border: 1.5px dashed #ffa500; background: #f8fafc; border-radius: 10px;
                    padding: 25px 10px; text-align: center; font-size: 14px;
                    font-weight: 500; color: #64748b; cursor: pointer;
                    transition: background 0.2s, box-shadow 0.2s;
                }
                #card-temperatura:hover { background: #f1f5f9; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
                #overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.15); backdrop-filter: blur(2px); z-index: 9998; }
                #popup { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #ffffff; border-radius: 12px; padding: 22px 26px; width: 320px; box-shadow: 0 6px 24px rgba(0,0,0,0.15); color: #2c3e50; z-index: 9999; }
                #popup h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #333; }
                #popup p { font-size: 15px; line-height: 1.4; margin: 0 0 16px 0; color: #555; }
                #popup button { background: #2563eb; border: none; color: #fff; font-size: 14px; padding: 8px 20px; border-radius: 8px; cursor: pointer; }
                </style>

                <div id="card-temperatura" onclick="abrirPopup()">
                    Temperatura<br>temporariamente inoperante
                </div>
                <div id="overlay" onclick="fecharPopup()"></div>
                <div id="popup">
                    <h3>Sensor Indisponível</h3>
                    <p>Pirômetro danificado.<br>Aguardando nova instalação.</p>
                    <button onclick="fecharPopup()">OK</button>
                </div>

                <script>
                function abrirPopup(){
                    document.getElementById('overlay').style.display = 'block';
                    document.getElementById('popup').style.display = 'block';
                }
                function fecharPopup(){
                    document.getElementById('overlay').style.display = 'none';
                    document.getElementById('popup').style.display = 'none';
                }
                </script>
            """
            components.html(popup_html, height=120)

        else:
            # Lógica padrão para todos os outros sensores
            st.subheader(f"Análise Anual para {config.NOMES_SENSORES.get(sensor, sensor)}")
            df_anual_plot = df_anual_filtrado.groupby(df_anual_filtrado['ANO'].dt.year)[sensor].mean().reset_index()

        # Agrupa os dados por ano e calcula a média para o sensor atual
        df_anual_plot = df_anual_filtrado.groupby(df_anual_filtrado['ANO'].dt.year)[sensor].mean().reset_index()
        
        if not df_anual_plot.empty:
            st.bar_chart(df_anual_plot.set_index('ANO')[sensor])
            st.caption(analysis.analisar_tendencia(df_anual_plot, sensor))
        else:
            st.info(f"Não há dados anuais suficientes para o sensor {sensor} neste período.")


