"""Imprime APENAS estrutura e contagem de arquivos, nunca linhas ou valores de produção."""
from collections import defaultdict
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
paths=sorted((ROOT/"data").glob("dados_detalhados_*.parquet"))
schemes=defaultdict(list)
print("PARQUET_FILES",len(paths))
for p in paths:
    try:
        pf=pq.ParquetFile(p)
        key=tuple((f.name,str(f.type)) for f in pf.schema_arrow)
        schemes[key].append(p.name)
    except Exception as error:
        print("FILE_ERROR",p.name,type(error).__name__)
for i,(schema, filenames) in enumerate(schemes.items()):
    print("SCHEMA",i,"FILES",len(filenames),"EXAMPLES",filenames[:3])
    for name,datatype in schema:
        print(" COLUMN",repr(name),datatype)
excel=ROOT/"data"/"dados_resumidos_gerado.xlsx"
if excel.exists():
    xls=pd.ExcelFile(excel)
    print("EXCEL_SHEETS",len(xls.sheet_names))
    for s in xls.sheet_names[:5]:
        print(" SHEET",repr(s),"COLS",list(pd.read_excel(xls,sheet_name=s,nrows=0).columns))
