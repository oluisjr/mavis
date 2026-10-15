"""Triagem por deslocamento e excursões, usando apenas médias diárias.

Avisos exploratórios, sem capacidade de diagnosticar falhas físicas.
"""
import numpy as np
import pandas as pd

def metricas(serie):
    valores=pd.to_numeric(serie,errors="coerce").replace([np.inf,-np.inf],np.nan).dropna()
    n=len(valores)
    if n<8:
        return {"estado":"indisponivel","indice":None,"motivo":"Menos de oito médias válidas."}
    janela=max(2,int(np.ceil(n*.2)))
    inicial=float(valores.iloc[:janela].median())
    final=float(valores.iloc[-janela:].median())
    if abs(inicial)<1e-9:
        return {"estado":"indisponivel","indice":None,"motivo":"Referência inicial próxima de zero."}
    mudanca=100*(final-inicial)/abs(inicial)
    excursao=100*float((valores-inicial).abs().max())/abs(inicial)
    anterior=valores.shift(1)
    saltos=(100*(valores-anterior).abs()/anterior.abs().where(anterior.abs()>1e-9)).dropna()
    salto=float(saltos.max()) if len(saltos) else 0.
    relevante=abs(mudanca)>=5 or excursao>=10 or salto>=8
    atencao=abs(mudanca)>=1 or excursao>=2 or salto>=2
    return {
        "estado":"relevante" if relevante else ("atencao" if atencao else "sem_gatilho"),
        "indice":round(min(100.,max(abs(mudanca)*10,excursao*5,salto*5)),1),
        "mudanca":round(mudanca,2),"excursao":round(excursao,2),"salto":round(salto,2),
    }
