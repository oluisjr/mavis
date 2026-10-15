"""Componentes de interface: filtros, clareza de unidades e acesso às páginas."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from . import config, session_manager

def hide_sidebar_nav():
    """Apenas estética: autorização real é verificada em cada página."""
    st.markdown("<style>[data-testid='stSidebarNav']{display:none;}</style>", unsafe_allow_html=True)

def hide_main_page_nav_and_footer():
    st.markdown("<style>footer{visibility:hidden;}</style>", unsafe_allow_html=True)

def render_mavis_header(theme: str = "light"):
    st.markdown(
        "<h1 style='font-weight:350;letter-spacing:.12em;margin-bottom:0'>MAVIS</h1>"
        "<p style='color:#637083;margin-top:0'>Monitoramento e Análise de Variáveis Industriais de Soldagem</p>",
        unsafe_allow_html=True,
    )

def _opcoes_unicas(df: pd.DataFrame, coluna: str) -> list[str]:
    if df.empty or coluna not in df:
        return []
    return sorted(df[coluna].dropna().astype("string").str.strip().unique().tolist())

def render_sidebar(df_total_completo: pd.DataFrame, page_name: str):
    session_manager.initialize_session_state()
    filtros = st.session_state.filtros_aplicados
    with st.sidebar:
        st.markdown("### Filtros de análise")
        if df_total_completo.empty:
            st.error("Histórico indisponível.")
            return
        todas_receitas = _opcoes_unicas(df_total_completo, "PROGRAM_Nº")
        receitas = todas_receitas + ["Todas"]
        if not todas_receitas:
            receitas = ["Todas"]
        # Mantém receita individual como padrão para não misturar condições operacionais.
        padrao = filtros.get("receita_fmt", "Todas")
        if padrao == "Todas" and "123" in receitas and not st.session_state.get("filtros_iniciados"):
            padrao = "123"
        if padrao not in receitas:
            padrao = todas_receitas[0] if todas_receitas else "Todas"
        tem_medidas = any(sensor in df_total_completo for sensor in config.NOMES_SENSORES)
        with st.form("filtros_mavis"):
            receita = st.selectbox("Receita / programa", receitas, index=receitas.index(padrao))
            subset = df_total_completo
            if receita != "Todas" and "PROGRAM_Nº" in subset:
                subset = subset.loc[subset["PROGRAM_Nº"].eq(receita).fillna(False)]
            permitir_codigos = tem_medidas
            with st.expander("Códigos de processo", expanded=False):
                if not permitir_codigos:
                    st.caption("Filtros por código desativados: falta a série bruta para reconstruir as médias.")
                codigo_entrada = _opcoes_unicas(subset, "code ENTRY")
                codigo_saida = _opcoes_unicas(subset, "code EXIT")
                entrada_atual = filtros.get("entry_code", "Todos")
                saida_atual = filtros.get("exit_code", "Todos")
                entrada = st.selectbox(
                    "Código de entrada", ["Todos", *codigo_entrada],
                    index=(["Todos", *codigo_entrada].index(entrada_atual) if entrada_atual in ["Todos", *codigo_entrada] else 0),
                    disabled=not permitir_codigos or not codigo_entrada,
                )
                saida = st.selectbox(
                    "Código de saída", ["Todos", *codigo_saida],
                    index=(["Todos", *codigo_saida].index(saida_atual) if saida_atual in ["Todos", *codigo_saida] else 0),
                    disabled=not permitir_codigos or not codigo_saida,
                )
            datas = subset["DATA"].dropna()
            anos = sorted(int(x) for x in datas.dt.year.unique())
            anos_atuais = [x for x in filtros.get("anos", []) if x in anos]
            anos_escolhidos = st.multiselect("Anos", anos, default=anos_atuais)
            meses = sorted(int(x) for x in datas.dt.month.unique())
            meses_atuais = [x for x in filtros.get("meses", []) if x in meses]
            meses_escolhidos = st.multiselect("Meses", meses, default=meses_atuais)
            semanas_escolhidas = []
            datas_escolhidas = []
            if page_name == "diaria":
                dias = sorted(datas.dt.strftime("%Y-%m-%d").unique().tolist())
                # Datas completas, não dias do mês.
                existentes = [x for x in filtros.get("dias", []) if x in dias]
                datas_escolhidas = st.multiselect("Dias específicos (opcional)", dias, default=existentes)
            if page_name in ("diaria", "mensal"):
                st.caption("Filtros vazios significam todos os valores.")
            submitted = st.form_submit_button("Aplicar filtros", use_container_width=True)
            if submitted:
                st.session_state.filtros_aplicados = {
                    "receita_fmt": receita,
                    "entry_code": entrada if permitir_codigos else "Todos",
                    "exit_code": saida if permitir_codigos else "Todos",
                    "anos": anos_escolhidos,
                    "meses": meses_escolhidos,
                    "semanas": semanas_escolhidas,
                    "dias": datas_escolhidas,
                }
                st.session_state.filtros_iniciados = True
                st.rerun()
        if filtros.get("receita_fmt") == "Todas":
            st.warning("A análise conjunta mistura receitas distintas. Não interpretar índices como diagnóstico de equipamento.")
        st.divider()
        if st.button("Encerrar sessão", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.filtros_aplicados = {
                k: list(v) if isinstance(v, list) else v
                for k, v in session_manager.DEFAULT_FILTERS.items()
            }
            st.switch_page("inicio.py")


def mensagens_de_origem(avisos: list[str]):
    for aviso in dict.fromkeys(avisos):
        st.warning(aviso)


def formatar_indice(valor: float | None) -> str:
    return f"{valor:.1f}/100" if valor is not None else "Indisponível"
