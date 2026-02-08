import pandas as pd
import numpy as np
from pathlib import Path
from utils import norm_text

#Tabla territorial base (llave: código DANE)

territorial=pd.read_csv(r"C:\Users\paper\Desktop\Master\tipos_ruralidad.csv").rename(columns={
    "Codigo_DANE":"codigo_dane",
    "Departamento":"departamento",
    "Municipio":"municipio",
    "Tipo_ruralidad":"tipo_ruralidad"
})
territorial["codigo_dane"]  =territorial["codigo_dane"].astype(str).str.strip()
territorial["depto_key"]    =norm_text(territorial["departamento"])
territorial["mun_key"]      =norm_text(territorial["municipio"])

#Fila por municipio (código DANE)
territorial_1=territorial.drop_duplicates(subset=["codigo_dane"]).copy()

# Mapa para asignar código DANE a fuentes que NO lo traen (por depto+municipio)
territorial_map=(
    territorial_1[["codigo_dane","depto_key","mun_key"]]
    .drop_duplicates(subset=["depto_key","mun_key"], keep="first")
    .copy()
)

# Escolaridad (agregación municipal + código DANE)
escolaridad=pd.read_csv(r"C:\Users\paper\Desktop\Master\escolaridad_municipios_tidy.csv").rename(columns={
    "Departamento": "departamento",
    "Municipio": "municipio",
    "valor": "valor_escolaridad"
})
escolaridad["depto_key"] =norm_text(escolaridad["departamento"])
escolaridad["mun_key"]   =norm_text(escolaridad["municipio"])

#Asignar codigo_dane usando el mapa territorial
escolaridad=escolaridad.merge(
    territorial_map,
    on=["depto_key", "mun_key"],
    how="left",
    validate="m:1"
)

#Total municipal
esc_total=(
    escolaridad.groupby("codigo_dane",as_index=False)
    .agg(escolaridad_total=("valor_escolaridad","sum"))
)

#Escolaridad por tipo_estudio
esc_tipo=(
    escolaridad.pivot_table(index="codigo_dane",columns="tipo_estudio",
                            values="valor_escolaridad",aggfunc="sum",fill_value=0)
    .reset_index()
)
esc_tipo.columns=["codigo_dane"] + [
    f"esc_{norm_text(pd.Series([c])).iloc[0].lower().replace(' ','_')}"
    for c in esc_tipo.columns[1:]
]

#Estrato (manzanas -> municipal)

estrato=pd.read_csv(r"C:\Users\paper\Desktop\Master\manzanas_estrato_por_municipio.csv").rename(columns={
    "DEPTO": "departamento",
    "MPIO": "municipio",
    "ESTRATO_PREDOMINANTE_INT": "estrato",
    "n_manzanas": "n_manzanas"
})
estrato["depto_key"] =norm_text(estrato["departamento"])
estrato["mun_key"]   =norm_text(estrato["municipio"])

estrato=estrato.merge(
    territorial_map,
    on=["depto_key", "mun_key"],
    how="left",
    validate="m:1"
)

estrato_valid=estrato.dropna(subset=["codigo_dane"]).copy()
estrato_valid["n_manzanas"]=pd.to_numeric(estrato_valid["n_manzanas"],errors="coerce").fillna(0)
estrato_valid["estrato"]=pd.to_numeric(estrato_valid["estrato"],errors="coerce")

#Estrato predominante = estrato con más manzanas
estrato_valid=estrato_valid.sort_values(["codigo_dane","n_manzanas"], ascending=[True,False])
estr_pred=(
    estrato_valid.groupby("codigo_dane",as_index=False)
    .head(1)[["codigo_dane", "estrato","n_manzanas"]]
    .rename(columns={"estrato":"estrato_predominante","n_manzanas":"n_manzanas_estrato_pred"})
)

# indicador adicional: proporción de manzanas en estratos 1-2 (bajos)
estrato_valid["manzanas_bajas"] = np.where(estrato_valid["estrato"].isin([1, 2]),
                                          estrato_valid["n_manzanas"], 0)

estr_bajo = (
    estrato_valid.groupby("codigo_dane", as_index=False)
    .agg(n_manzanas_total=("n_manzanas", "sum"),
         n_manzanas_bajas=("manzanas_bajas", "sum"))
)
estr_bajo["prop_manzanas_bajas_1_2"]=np.where(
    estr_bajo["n_manzanas_total"]>0,
    estr_bajo["n_manzanas_bajas"]/estr_bajo["n_manzanas_total"],
    np.nan
)

#Población (último año disponible por municipio)

poblacion=pd.read_csv(r"C:\Users\paper\Desktop\Master\proyección_poblacion.csv").rename(columns={
    "DP": "codigo_dane",
    "AÑO": "anio",
    "DPNOM": "departamento",
    "Población": "poblacion"
})
poblacion["codigo_dane"]=poblacion["codigo_dane"].astype(str).str.strip()
poblacion["anio"]=pd.to_numeric(poblacion["anio"], errors="coerce")
poblacion["poblacion"]=pd.to_numeric(poblacion["poblacion"], errors="coerce")

poblacion_ult=(
    poblacion.sort_values(["codigo_dane", "anio"])
    .groupby("codigo_dane", as_index=False)
    .tail(1)[["codigo_dane", "anio", "poblacion"]]
    .rename(columns={"anio": "anio_poblacion"})
)

#Dataframe maestro municipal (1 fila = 1 municipio)

df_master = (
    territorial_1[["codigo_dane","departamento","municipio","tipo_ruralidad"]]
    .merge(esc_total,on="codigo_dane",how="left")
    .merge(esc_tipo,on="codigo_dane",how="left")
    .merge(estr_pred,on="codigo_dane",how="left")
    .merge(estr_bajo[["codigo_dane","n_manzanas_total","prop_manzanas_bajas_1_2"]],on="codigo_dane",how="left")
    .merge(poblacion_ult,on="codigo_dane",how="left")
)

#Pasamos a evaluar población a nivel departamental (quitamos las variables anteriores relacionadas)
# Normalizar nombres de departamento
poblacion["departamento"]=(
    poblacion["departamento"]
    .astype(str)
    .str.upper()
    .str.strip()
)

df_master["departamento"]=(
    df_master["departamento"]
    .astype(str)
    .str.upper()
    .str.strip()
)

pob_depto = (
    poblacion
    .sort_values(["departamento","anio"])
    .groupby("departamento",as_index=False)
    .tail(1)
    [["departamento","anio","poblacion"]]
    .rename(columns={
        "anio":"anio_poblacion_departamental",
        "poblacion":"poblacion_departamental"
    })
)

#Eliminar columnas municipales inválidas

cols_a_eliminar = [c for c in ["poblacion", "anio_poblacion"] if c in df_master.columns]
df_master = df_master.drop(columns=cols_a_eliminar)

df_master = df_master.merge(
    pob_depto,
    on="departamento",
    how="left",
    validate="m:1"
)

# 6) Diagnóstico y guardado

diagnostico=pd.DataFrame({
    "columna":df_master.columns,
    "nulos":[int(df_master[c].isna().sum()) for c in df_master.columns],
    "pct_nulos":[float(df_master[c].isna().mean()) for c in df_master.columns],
}).sort_values("pct_nulos",ascending=False)

print("Filas:",df_master.shape[0],"| Columnas:",df_master.shape[1])
print("Duplicados código_dane:",df_master["codigo_dane"].duplicated().sum())
print("\nTop nulos:\n",diagnostico.head(10))

out_path=Path("df_master_municipal.csv")
df_master.to_csv(out_path, index=False, encoding="utf-8")
print("\nGuardado en:", out_path.resolve())
