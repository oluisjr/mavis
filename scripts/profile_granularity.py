"""Auditoria estrutural agregada; não revela valores de sensores ou IDs particulares."""
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]/"data"
for name in ("123","1","2","9999"):
    f=ROOT/f"dados_detalhados_{name}.parquet"
    if not f.exists():continue
    cols=["WELDNº","DATA","DATAHORA","ID_PONTO","PROGRAM_Nº","MeasP"]
    df=pd.read_parquet(f,columns=cols)
    for col in ["DATAHORA","DATA"]:
        df[col]=pd.to_datetime(df[col],errors="coerce")
    print("FILE_PROFILE",name,"ROWS",len(df),"MISSING_TIME_PCT",round(df["DATAHORA"].isna().mean()*100,1))
    for grouping in (["WELDNº"],["DATA","WELDNº"],["DATAHORA","WELDNº"],["DATA","WELDNº","MeasP"]):
        counts=df.groupby(grouping,dropna=False).size()
        print(" GROUP",repr(grouping),"GROUPS",len(counts),"SIZE_MED",float(counts.median()),"SIZE_P90",float(counts.quantile(.9)),"SIZE_MAX",int(counts.max()),"GT1_PCT",round((counts>1).mean()*100,1))
    print(" ID_PONTO unique ratio",round(df["ID_PONTO"].nunique()/max(1,len(df)),5))
    print(" DATAHORA unique ratio",round(df["DATAHORA"].nunique()/max(1,len(df)),5))
    print(" DATAHORA_monotonic",bool(df["DATAHORA"].is_monotonic_increasing))
    print(" WELDNº_NULL",round(df["WELDNº"].isna().mean()*100,2),"MEASP_NUNIQUE",df["MeasP"].nunique())
