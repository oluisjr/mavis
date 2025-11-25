import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from app import config, data_loader, ui_components, analysis, session_manager

# --- Lógica de Controle de Erro e Configuração da Página ---

# ============================================================
# VERIFICA LOGIN
# ============================================================
if not st.session_state.get('authenticated', False):
    st.error("Acesso negado. Por favor, faça o login na página principal.")
    st.stop()


if 'error_occurred' not in st.session_state:
    st.session_state.error_occurred = False

if st.session_state.error_occurred:
    favicon = config.FAVICON_ERRO_PATH
    logo = config.LOGO_ERRO_PATH
    page_title = "MAVIS - Erro"
else:
    favicon = config.FAVICON_PATH
    logo = config.LOGO_PATH
    page_title = "MAVIS - Sumário Executivo"

st.set_page_config(
    page_title=page_title,
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=favicon
)

ui_components.hide_main_page_nav_and_footer()

# ### MUDANÇA 2: Renderização do cabeçalho movida para o topo ###
# O cabeçalho agora é desenhado ANTES de qualquer carregamento de dados demorado.
image, title, blank = st.columns([1, 3, 1], vertical_alignment="center")
with image:
    st.image(logo, width=80)
with title:
    # Em caso de erro, mostramos um título simples, senão o interativo
    if st.session_state.error_occurred:
        ui_components.render_mavis_header(theme='error')
    else:
        ui_components.render_mavis_header()

df_total_completo = data_loader.carregar_dados_iniciais()
# Para o sumário, usaremos o filtro 'anual' que é o mais simples (receita, código, ano)
ui_components.render_sidebar(df_total_completo, page_name='anual')

filtros = st.session_state.get('filtros_aplicados', {})
receita_str = filtros.get('receita_fmt', '1')

# Se estivermos em modo de erro, exiba a mensagem e pare a execução.
if st.session_state.error_occurred:
    st.error(
        """
        **A aplicação encontrou um problema inesperado.**
        Isso pode ter sido causado por um arquivo de dados ausente, corrompido ou uma falha interna.
        Por favor, verifique a configuração e os arquivos de dados.
        Se o problema persistir, contate o suporte.
        """
    )
    if 'last_error' in st.session_state:
        st.code(st.session_state.last_error)
    st.stop()

# --- Bloco Principal da Aplicação ---
    st.session_state.error_occurred = False

# --- LÓGICA DE CARREGAMENTO DE DADOS ---
filtros = st.session_state.get('filtros_aplicados', {})
receita_str = filtros.get('receita_fmt', '1') # Padrão para '123' se algo falhar

(df_total, df_diario, df_semanal, df_mensal, df_anual), messages = data_loader.carregar_dados_por_receita(receita_str)

# Calcula e armazena os riscos para uso no painel
riscos_dia = {}
if not df_diario.empty:
    riscos_dia = {s: analysis.simular_risco_por_regras(df_diario, s) for s in config.NOMES_SENSORES.keys()}

riscos_mes = {}
if not df_mensal.empty:
    riscos_mes = {s: analysis.simular_risco_por_regras(df_mensal, s) for s in config.NOMES_SENSORES.keys()}

data_hora_brasilia = datetime.now(ZoneInfo('America/Sao_Paulo'))
st.caption(f"Análise baseada nos dados filtrados até {data_hora_brasilia.strftime('%d/%m/%Y')}.")

riscos_para_analise = riscos_dia if riscos_dia else riscos_mes

def get_formatted_sensor_name(sensor_key: str) -> str:
    full_name = config.NOMES_SENSORES.get(sensor_key, str(sensor_key))
    if isinstance(full_name, str):
        return full_name.split(' (')[0]
    return str(sensor_key)

if not riscos_para_analise:
    st.warning("Não há dados de risco disponíveis para gerar o Sumário Executivo.")
else:
    st.subheader("Health Score por Sensor")

    sensores = list(config.NOMES_SENSORES.keys())
    cols = st.columns(len(sensores))

    for i, sensor in enumerate(sensores):
        with cols[i]:
            if sensor == "TEMPERATURA":
                # Mensagem clicável com popup
                popup_html = """
                <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

                body, p, h3, button, div {
                font-family: 'Inter', sans-serif;
                }
                
                #overlay {
                display: none;
                position: fixed;
                inset: 0;
                background: rgba(0,0,0,0.15);
                backdrop-filter: blur(2px);
                z-index: 9998;
                }

                
                #popup {
                display: none;
                position: fixed;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                background: #ffffff;
                border-radius: 12px;
                padding: 22px 26px;
                width: 320px;
                max-width: 90vw;
                box-shadow: 0 6px 24px rgba(0,0,0,0.15);
                color: #2c3e50;
                z-index: 9999;
                animation: fadeIn 0.25s ease;
                }

                @keyframes fadeIn {
                from {opacity: 0; transform: translate(-50%, -48%);}
                to {opacity: 1; transform: translate(-50%, -50%);}
                }

                #popup h3 {
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 8px;
                color: #333;
                }

                #popup p {
                font-size: 15px;
                line-height: 1.4;
                margin: 0 0 16px 0;
                color: #555;
                }

                
                #popup button {
                background: #2563eb;
                border: none;
                color: #fff;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 20px;
                border-radius: 8px;
                cursor: pointer;
                transition: background 0.2s;
                }
                #popup button:hover {
                background: #1e4fcf;
                }

                
                #card-temperatura {
                border: 1.5px dashed #ffa500;
                background: #f8fafc;
                border-radius: 10px;
                padding: 25px 10px;
                text-align: center;
                font-size: 14px;
                font-weight: 500;
                color: #64748b;
                cursor: pointer;
                transition: background 0.2s, box-shadow 0.2s;
                }
                #card-temperatura:hover {
                background: #f1f5f9;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                }
                </style>

                <div id="card-temperatura" onclick="abrirPopup()">
                Temperatura<br>temporariamente <br> inoperante
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

                components.html(popup_html, height=160)
            else:
                risco = riscos_para_analise.get(sensor, 0)
                score = analysis.calcular_health_score(risco)
                nome_formatado = get_formatted_sensor_name(sensor)
                st.markdown(f"<p style='text-align: center; font-weight: bold;'>{nome_formatado}</p>", unsafe_allow_html=True)
                gauge_html = ui_components.render_liquid_chart_individual(score, nome_formatado)
                centered_liquid_html = f"""<div style="display: flex; justify-content: center; align-items: center; height: 150px; width: 100%;">{gauge_html}</div>"""
                components.html(centered_liquid_html, height=180)

    
    st.markdown("---")
    col_financeiro, col_foco = st.columns(2)

    riscos_numericos = {s: r for s, r in riscos_para_analise.items() if isinstance(r, (int, float))}

    if riscos_numericos:
        
        col_nada, col_foco, col_causa = st.columns([1, 2, 4], vertical_alignment="center")
        
        with col_foco:
            st.subheader("Foco no Ponto Crítico")
            
            sensores_validos = { # Remove temperatura
                sensor: risco
                for sensor, risco in riscos_numericos.items()
                if sensor != "TEMPERATURA"
            }

            if sensores_validos:
                sensores_ordenados = sorted(
                    sensores_validos.items(),
                    key=lambda item: item[1],
                    reverse=True
                )

                sensor_critico, risco_critico = sensores_ordenados[0]
                score_critico = analysis.calcular_health_score(risco_critico)
                nome_critico = get_formatted_sensor_name(sensor_critico)

                gauge_foco_html = ui_components.render_liquid_chart_foco(score_critico, nome_critico)
                centered_liquid_html = f"""<div style="display: flex; justify-content: center; align-items: center; height: 190px; width: 100%;">{gauge_foco_html}</div>"""
                components.html(centered_liquid_html, height=220)

            else:
                # Caso todos os sensores estejam inoperantes
                st.info("Nenhum sensor disponível para análise crítica no momento.")

        with col_causa:
        
            nome_critico_completo = config.NOMES_SENSORES.get(sensor_critico, sensor_critico)
            st.subheader(f"Análise de Causa Raiz e Recomendações para {sensor_critico}")
            analise_rca = analysis.analisar_causa_raiz(sensor_critico)
            
            col_causa, col_acao = st.columns(2)
            with col_causa:
                with st.container(border=True):
                    st.markdown("##### Causas Prováveis")
                    for causa in analise_rca['causas_provaveis']:
                        st.markdown(causa)

            with col_acao:
                with st.container(border=True):
                    st.markdown("##### Ações Recomendadas")
                    for acao in analise_rca['acoes_recomendadas']:
                        st.markdown(acao)
    else:
        with col_foco:
            st.info("Não há riscos numéricos calculados para determinar um ponto crítico.")
            
    st.markdown("---")
    st.caption("Developed by *Luis Ignacio* - 2025")






