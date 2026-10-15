"""Smoke test integral sem imprimir registros ou medições de produção."""
import time
from app import weld_loader, weld_analysis

def main():
    recipes = weld_loader.listar_receitas_detalhadas()
    if "123" not in recipes:
        print("SEM_DADOS_DETALHADOS")
        return
    inicio = time.perf_counter()
    pontos = weld_loader.carregar_pontos("123")
    t1=time.perf_counter()
    caracteristicas = weld_analysis.caracteristicas_por_solda(pontos)
    t2=time.perf_counter()
    painel, alertas = weld_analysis.analisar_soldas(caracteristicas)
    t3=time.perf_counter()
    assert len(caracteristicas) == len(painel)
    assert len(painel) > 1000
    assert not pontos.empty
    assert painel["WELDNº"].is_unique
    assert not painel["n_referencias"].isna().any()
    assert painel["n_referencias"].ge(0).all()
    print("WELD_VALIDATION_SUCCESS")
    print("WELDS_VALIDATED", len(painel))
    print("BASELINE_COVERAGE_PCT",round(100*panel_coverage(painel),1))
    print("STEPS_SECONDS",round(t1-inicio,1),round(t2-t1,1),round(t3-t2,1))
    # Dados brutos, curvas individuais e sensores não são impressos.

def panel_coverage(painel):
    return float(painel["n_referencias"].gt(0).mean())
if __name__ == "__main__":
    main()
