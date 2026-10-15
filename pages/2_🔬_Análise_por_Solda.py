"""Análise de alta resolução por solda, preservando os pontos individuais."""
import streamlit as st
import pandas as pd
from app import config, session_manager, ui_components, weld_loader, weld_analysis, weld_pipeline

st.set_page_config(page_title="MAVIS | Solda a solda", page_icon=config.FAVICON_PATH, layout="wide")
session_manager.check_authentication()
ui_components.hide_main_page_nav_and_footer()
ui_components.render_mavis_header()
st.title("Diagnóstico exploratório solda a solda")
st.caption(
    "A análise usa a sequência de ID_PONTO de cada solda. Não converte esse índice em segundos: "
    "a frequência real de amostragem não está disponível. Resultados são indícios estatísticos, "
    "não confirmação de falhas nem probabilidade de falha iminente."
)
receitas = weld_loader.listar_receitas_detalhadas()
if not receitas:
    st.error("Arquivos de leituras detalhadas não disponíveis. A média diária não permite esta análise.")
    st.stop()
receita = st.selectbox("Receita de soldagem", receitas,
                       index=receitas.index("123") if "123" in receitas else 0)
try:
    painel, alertas = weld_pipeline.analisar_receita(receita)
except (ValueError, FileNotFoundError, RuntimeError, OSError) as erro:
    st.error(f"Não foi possível analisar a receita: {erro}")
    st.stop()
if painel.empty:
    st.warning("Não existem soldas analisáveis nessa receita.")
    st.stop()

ultimas = st.select_slider("Janela de visualização (soldas mais recentes)",
                            options=[25, 50, 100, 200, 500], value=100)
visiveis = painel.tail(ultimas).copy()
n_disponiveis = int(visiveis["situacao"].eq("Sem referência contextual").sum())
n_alta = int(visiveis["situacao"].eq("Investigação prioritária").sum())
n_variacao = int(visiveis["situacao"].eq("Variação a investigar").sum())
col1, col2, col3, col4 = st.columns(4)
col1.metric("Soldas exibidas", len(visiveis))
col2.metric("Investigações prioritárias", n_alta)
col3.metric("Variações a investigar", n_variacao)
col4.metric("Sem referência suficiente", n_disponiveis)
if n_alta:
    st.error(
        f"Foram identificadas {n_alta} soldas com desvios estatísticos prioritários "
        "nesta janela. Ação recomendada: conferir os registros e confrontar a ocorrência "
        "com medições e limites homologados pela equipe de processo/manutenção."
    )
elif n_disponiveis:
    st.warning("Parte das soldas não possui referência comparável suficiente. Sem alerta NÃO significa ausência de falha.")
else:
    st.info("Sem ocorrências prioritárias pela heurística atual. Isso não descarta defeitos não observáveis pelos sensores.")

tab_soldas, tab_perfil, tab_metodo = st.tabs(["Ocorrências e evidências", "Curva da solda", "Critérios e limites"])

with tab_soldas:
    st.markdown("**Triagem das soldas mais recentes**")
    st.dataframe(visiveis[[
        "DATAHORA", "WELDNº", "contexto", "amostras", "situacao", "n_evidencias", "forca_maxima"
    ]].sort_values("DATAHORA", ascending=False), use_container_width=True, hide_index=True)
    if not alertas.empty:
        selecionados = alertas.loc[alertas["WELDNº"].isin(visiveis["WELDNº"])]
        if not selecionados.empty:
            st.markdown("**Evidências registradas**")
            st.dataframe(
                selecionados.sort_values("DATAHORA", ascending=False),
                use_container_width=True, hide_index=True
            )
    st.caption("Magnitude robusta é distância estatística a uma referência anterior. "
               "Não representa risco percentual, limite técnico nem número de sigmas de uma distribuição normal.")

with tab_perfil:
    soldas = visiveis.sort_values("DATAHORA", ascending=False)["WELDNº"].tolist()
    destaque = visiveis.loc[visiveis["n_evidencias"].gt(0), "WELDNº"].tolist()
    inicial = soldas.index(destaque[-1]) if destaque and destaque[-1] in soldas else 0
    solda = st.selectbox("Solda para investigação", soldas, index=inicial,
                         format_func=lambda num: f"Solda {int(num)}")
    sensores = [nome for nome in config.NOMES_SENSORES if nome not in config.SENSORES_INDISPONIVEIS]
    sensor = st.selectbox("Variável monitorada", sensores,
                          format_func=lambda nome: config.NOMES_SENSORES[nome])
    # Dados ponto a ponto recuperados apenas para desenhar a curva selecionada.
    pontos = weld_loader.carregar_pontos(receita)
    curva, n_ref = weld_analysis.perfil_com_referencia(pontos, solda, sensor)
    if curva.empty:
        st.warning("Não há medições válidas para esta combinação.")
    else:
        st.line_chart(curva, height=390, use_container_width=True)
        st.caption(f"Comparação por posição ID_PONTO. Soldas anteriores de referência: {n_ref}. "
                   "Envelope P05/P95 é empírico e não representa tolerância aprovada.")
        if n_ref < weld_analysis.MIN_REFERENCE:
            st.warning("Curva histórica de referência insuficiente. Somente a solda selecionada está representada.")
        st.markdown("**Informações do registro**")
        registro = visiveis.loc[visiveis["WELDNº"].eq(solda)]
        st.dataframe(registro, use_container_width=True, hide_index=True)

with tab_metodo:
    st.markdown("""
    **O que é medido:** mediana da solda, amplitude P95–P05, P95 das diferenças
    entre pontos sucessivos e P99 dos resíduos em relação à mediana móvel de 9 pontos.

    **Com quem se compara:** até 48 soldas anteriores, da mesma receita e dos
    mesmos códigos de entrada, saída e MeasP. São exigidas pelo menos 12 referências.
    Nenhuma solda posterior participa do cálculo.

    **Sinalização:** magnitude robusta acima de 3,5 entra em observação;
    desvios mais acentuados ou em múltiplas métricas tornam a investigação prioritária.
    Pequenas mudanças concordantes em quatro soldas consecutivas do mesmo
    contexto também são registradas para investigação, mesmo que individualmente
    não atinjam 3,5. Esses limiares são de triagem exploratória e precisam ser calibrados com
    eventos reais e tolerâncias aprovadas pela engenharia.

    **Limitações:** uma média por solda ainda é pouco para detectar oscilações,
    por isso a curva completa é preservada. A detecção de falhas elétricas
    como fusível trincado não pode ser confirmada só pela corrente da solda;
    medições de tensão, corrente em alta frequência, histórico de alarmes e inspeção
    do circuito podem ser necessárias. O sistema não executa comandos de produção.
    """)
