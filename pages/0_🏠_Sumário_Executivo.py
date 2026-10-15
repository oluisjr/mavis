"""Painel executivo com indicadores heurísticos transparentes."""
import streamlit as st
from app import analysis, config, data_loader, session_manager, ui_components, weld_loader, weld_pipeline

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

# A análise por solda deve preceder os agregados: médias podem esconder oscilações.
receita_detalhe = str(filtros.get("receita_fmt", "Todas"))
if receita_detalhe in weld_loader.listar_receitas_detalhadas():
    try:
        resumo_soldas, _ = weld_pipeline.analisar_receita(receita_detalhe)
        ultimas_soldas = resumo_soldas.tail(50)
        criticas = int(ultimas_soldas["situacao"].eq("Investigação prioritária").sum())
        variacoes = int(ultimas_soldas["situacao"].eq("Variação a investigar").sum())
        sem_referencia = int(ultimas_soldas["situacao"].eq("Sem referência contextual").sum())
        if criticas:
            st.error(
                f"Monitoramento ponto a ponto: {criticas} soldas com evidências prioritárias "
                f"nas últimas {len(ultimas_soldas)} soldas registradas. "
                "Investigar as curvas originais antes de interpretar as médias."
            )
        elif variacoes or sem_referencia:
            st.warning(
                f"Análise ponto a ponto: {variacoes} soldas com variações a investigar "
                f"e {sem_referencia} sem referência suficiente nas últimas "
                f"{len(ultimas_soldas)} soldas."
            )
        else:
            st.info("Nenhum desvio prioritário nas últimas soldas pelo método atual. "
                    "Isso não descarta defeitos físicos.")
        st.page_link("pages/2_🔬_Análise_por_Solda.py",
                     label="Abrir investigação solda a solda e curvas originais", icon="🔬")
        st.caption("Os dados são históricos, não há aquisição em tempo real integrada.")
    except (ValueError, OSError, RuntimeError) as erro:
        st.warning(f"Análise ponto a ponto indisponível: {erro}")
else:
    st.warning("Sem Parquet detalhado nesta receita. As médias diárias podem mascarar falhas rápidas.")

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
