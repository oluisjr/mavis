"""Smoke test da navegação: confirma que as páginas executam em Streamlit."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "0_🏠_Sumário_Executivo.py",
    "1_📈_Análise_Diária.py",
    "3_🗓️_Análise_Mensal.py",
    "4_📊_Análise_Anual.py",
)

@pytest.mark.parametrize("arquivo", PAGES)
def test_pagina_carrega_sem_excecoes(arquivo):
    app = AppTest.from_file(str(ROOT / "pages" / arquivo), default_timeout=90)
    app.session_state["authenticated"] = True
    # AppTest executa cada arquivo como entrypoint isolado; não registra a navegação
    # multipágina do inicio.py. O link funciona no app real, não nesse harness.
    from unittest.mock import patch
    with patch("streamlit.page_link"):
        app.run()
    assert not app.exception, f"Erro de inicialização: {arquivo}: {app.exception}"
