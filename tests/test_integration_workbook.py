"""Integração real: usa somente o workbook versionado, sem publicar amostras."""
from pathlib import Path
import pandas as pd
import pytest
from app import config, data_loader


@pytest.mark.integration
def test_planilha_versionada_abre_e_gera_visoes():
    origem = config.DATA_DIR / "dados_resumidos_gerado.xlsx"
    if not origem.exists():
        pytest.skip("Base de integração não distribuída neste ambiente.")
    base = data_loader.carregar_dados_iniciais()
    assert not base.empty, "A aba Dados Completos deve ser legível e conter datas válidas."
    assert "DATA" in base
    assert "PROGRAM_Nº" in base
    receitas = base["PROGRAM_Nº"].dropna().unique().tolist()
    assert receitas, "Nenhuma receita válida identificada."
    escolhida = "123" if "123" in receitas else str(receitas[0])
    filtros = {
        "receita_fmt": escolhida,
        "entry_code": "Todos",
        "exit_code": "Todos",
        "anos": [], "meses": [], "semanas": [], "dias": [],
    }
    visoes, avisos = data_loader.obter_visoes_filtradas(filtros)
    assert any(not quadro.empty for quadro in visoes.values()), (
        "A base selecionada deve fornecer ao menos uma série de análise; "
        "verifique nomes das colunas e abas do Excel."
    )
    for granularidade, dados in visoes.items():
        if not dados.empty:
            assert data_loader.COLUNAS_DATA[granularidade] in dados
            assert dados[data_loader.COLUNAS_DATA[granularidade]].is_monotonic_increasing
