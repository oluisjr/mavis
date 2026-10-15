"""Execução em cache para uma única receita e um conjunto fechado de sensores."""
import streamlit as st
from . import weld_loader, weld_analysis

@st.cache_data(ttl=900, max_entries=2, show_spinner="Analisando as curvas individuais e suas referências históricas...")
def analisar_receita(receita: str):
    pontos = weld_loader.carregar_pontos(receita)
    atributos = weld_analysis.caracteristicas_por_solda(pontos)
    painel, evidencias = weld_analysis.analisar_soldas(atributos)
    return painel, evidencias

