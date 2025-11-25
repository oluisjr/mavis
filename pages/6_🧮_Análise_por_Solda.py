import streamlit as st
import pandas as pd
from app import config, analysis, ui_components, data_loader
import streamlit.components.v1 as components

# ============================================================
# VERIFICA LOGIN
# ============================================================
if not st.session_state.get('authenticated', False):
    st.error("Acesso negado. Por favor, faça o login na página principal.")
    st.stop()
    st.navigation(main.py)

# ============================================================
# CONFIGURAÇÕES DA PÁGINA
# ============================================================
favicon = config.FAVICON_PATH
page_title = "MAVIS – Análise Detalhada (Parquet)"

st.set_page_config(
    page_title=page_title,
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=favicon
)

ui_components.hide_main_page_nav_and_footer()

df_total_completo = data_loader.carregar_dados_iniciais()
# A página chama a sua própria sidebar, passando o identificador 'diaria'
ui_components.render_sidebar(df_total_completo, page_name='diaria')

# ============================================================
# CARREGA OS DADOS DOS PARQUETS
# ============================================================
st.subheader("📊 Análise Detalhada dos Sensores (Parquet)")

filtros = st.session_state.get('filtros_aplicados', {})
receita_str = filtros.get("receita_fmt", "123")

df_parquet = data_loader.carregar_parquet_por_receita(receita_str)

if df_parquet.empty:
    st.warning("Nenhum dado detalhado encontrado para esta receita.")
    st.stop()

# Converte DATAHORA → datetime e cria coluna DATA somente para filtros
df_parquet["DATAHORA"] = pd.to_datetime(df_parquet["DATAHORA"], errors="coerce")
df_parquet["DATA"] = df_parquet["DATAHORA"].dt.date


# ============================================================
# SIDEBAR PADRÃO DA APLICAÇÃO
# ============================================================
df_fake = pd.DataFrame({"DATA": df_parquet["DATA"]})
ui_components.render_sidebar(df_fake, page_name='detalhada')


# ============================================================
# FILTROS
# ============================================================
df_final = df_parquet.copy()

if filtros.get('anos'):
    df_final = df_final[df_final["DATAHORA"].dt.year.isin(filtros["anos"])]

if filtros.get('meses'):
    df_final = df_final[df_final["DATAHORA"].dt.month.isin(filtros["meses"])]

if filtros.get('dias'):
    df_final = df_final[df_final["DATAHORA"].dt.day.isin(filtros["dias"])]

if df_final.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()


# ============================================================
# CABEÇALHO
# ============================================================
image, title, blank = st.columns([1, 4, 1], vertical_alignment="center")
with image:
    st.image(config.LOGO_PATH, width=80)
with title:
    ui_components.render_mavis_header(theme=st.session_state.get("theme", "light"))

st.markdown("### 📍 Relatório Detalhado por Ponto de Medição")


# ============================================================
# GRÁFICOS E ANÁLISES
# ============================================================
sensores = list(config.CORES.keys())  # usa o mesmo dicionário da página diária

col1, col2 = st.columns(2)

# Dividimos sensores iguais ao layout original
sensores_col1 = sensores[:2]
sensores_col2 = sensores[2:4]

# ============================================================
# FUNÇÃO PARA DESENHAR BLOCO DE SENSOR
# ============================================================
def render_bloco_sensor(df, sensor):
    st.write(f"## {config.NOMES_SENSORES[sensor]}")

    # Métrica de risco
    risco = analysis.simular_risco_por_regras(df, sensor)
    score = analysis.calcular_health_score(risco)

    liquid_html = ui_components.render_mini_liquid_chart(score)
    liquid_center = (
        f"<div style='display:flex;justify-content:center;"
        f"align-items:center;height:60px;width:100%;'>{liquid_html}</div>"
    )
    components.html(liquid_center, height=80)

    # status textual
    st.markdown(analysis.detectar_anomalia(df, sensor))

    # gráfico temporal
    st.line_chart(df.set_index("DATAHORA")[sensor])

    # análise avançada
    with st.expander("Ver análise detalhada da IA"):
        st.caption(analysis.analisar_tendencia(df, sensor, sensor=sensor))
        st.markdown("---")

        st.write("**Potencial de falha iminente (%)**")
        if risco > 75:
            st.error(f"Risco Elevado: {risco:.1f}%")
        elif risco > 50:
            st.warning(f"Atenção: {risco:.1f}%")
        elif risco > 20:
            st.info(f"Risco Moderado: {risco:.1f}%")
        else:
            st.success(f"Risco Baixo: {risco:.1f}%")

        status = analysis.detectar_anomalia(df, sensor)
        if "Normal" not in status:
            st.markdown("---")
            st.write("**Análise de Causa Raiz:**")
            rca = analysis.analisar_causa_raiz(sensor)
            st.caption("**Causas Prováveis:**\n" + "\n".join(rca["causas_provaveis"]))
            st.caption("**Ações Recomendadas:**\n" + "\n".join(rca["acoes_recomendadas"]))
        else:
            st.info("Tudo normal por aqui...")


# ============================================================
# COLUNA 1
# ============================================================
with col1:
    for sensor in sensores_col1:
        render_bloco_sensor(df_final, sensor)


# ============================================================
# COLUNA 2
# ============================================================
with col2:
    for sensor in sensores_col2:
        render_bloco_sensor(df_final, sensor)


# ============================================================
# SENSORES SEM DADOS (MESMO LAYOUT)
# ============================================================
sensor_atual = sensores[4]
st.write(f"## :red[{config.NOMES_SENSORES[sensor_atual]}]")

for sensor in sensores[4:]:
    st.markdown("### ⚠️ :gray-background[Sensor inoperante, impossível analisar!] ⚠️")
