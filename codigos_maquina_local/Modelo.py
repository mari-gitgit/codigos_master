#Imports y config

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import re
from unidecode import unidecode

MUNICIPAL_PATH="df_master_derived.csv"
DESERCION_XLSX="articles-415244_recurso_7.xlsx"
OUT_DIR="output_model"
FIG_DIR=os.path.join(OUT_DIR, "figures")
TAB_DIR=os.path.join(OUT_DIR, "tables")

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TAB_DIR, exist_ok=True)

def norm_depto(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unidecode(s)                 # quita tildes
    s = re.sub(r"\s+", " ", s)       # espacios dobles
    s = s.replace(".", "").replace(",", "")
    s = s.replace(" D C", " DC")     # arreglos comunes
    s = s.replace("D C", "DC")
    # normalizaciones comunes en Colombia
    s = s.replace("BOGOTA DC", "BOGOTA")
    s = s.replace("BOGOTA D C", "BOGOTA")
    s = s.replace("ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA", "SAN ANDRES")
    return s

#Cargar base municipal y construir derivadas

df_mun = pd.read_csv(MUNICIPAL_PATH)

#Educación superior agregada (asegura que existan columnas)
superior_parts = [
    "esc_tecnica_profesional",
    "esc_tecnologica",
    "esc_profesional",
    "esc_especializacion",
    "esc_maestria",
    "esc_doctorado"
]

missing_cols=[c for c in superior_parts + ["escolaridad_total"] if c not in df_mun.columns]
if missing_cols:
    raise ValueError(f"Faltan columnas necesarias en df_mun: {missing_cols}")

df_mun["esc_superior"]=df_mun[superior_parts].sum(axis=1)

#Proporción superior (evita división por cero)
df_mun["prop_superior"]=df_mun["esc_superior"]/df_mun["escolaridad_total"].replace({0:np.nan})

#Indicador de “municipio rural”
df_mun["is_rural"]=df_mun["tipo_ruralidad"].isin(["Rural","Rural disperso"]).astype(int)


# Agregar a nivel departamento
# estas X quedan constantes por depto

df_depto=(
    df_mun
    .groupby("departamento", as_index=False)
    .agg(
        prop_superior_mean=("prop_superior","mean"),
        estrato_pred_mean=("estrato_predominante","mean"),
        rural_share=("is_rural","mean"),
        n_municipios=("codigo_dane","count")
    )
)

df_depto.to_csv(os.path.join(TAB_DIR,"01_X_departamental.csv"),index=False)


#Extraer y limpiar deserción departamental desde Excel
#Nota: este Excel tiene una estructura con header “desplazado”.

td_raw=pd.read_excel(DESERCION_XLSX,sheet_name="TD - departamento",header=11)

td=td_raw.copy()
td=td.rename(columns={td.columns[0]: "departamento"})

#La primera fila tiene los años en las columnas
year_row=td.iloc[0]
year_cols={}
for c in td.columns[1:]:
    val=year_row[c]
    if pd.notna(val):
        year_cols[c] = int(val)

td=td.drop(index=0).reset_index(drop=True)
td=td[["departamento"] + list(year_cols.keys())].rename(columns=year_cols)

#Largo (panel)
td_long=td.melt(id_vars="departamento",var_name="anio",value_name="tasa_desercion")

td_long["departamento"]=td_long["departamento"].astype(str).str.strip()
td_long["anio"]=pd.to_numeric(td_long["anio"], errors="coerce")
td_long["tasa_desercion"]=pd.to_numeric(td_long["tasa_desercion"], errors="coerce")

td_long=td_long.dropna(subset=["departamento","anio","tasa_desercion"])
td_long["anio"]=td_long["anio"].astype(int)

td_long.to_csv(os.path.join(TAB_DIR,"02_desercion_panel_long.csv"), index=False)

#Construir panel final departamento-año

df_depto["depto_key"] = df_depto["departamento"].apply(norm_depto)
td_long["depto_key"] = td_long["departamento"].apply(norm_depto)

df_model = td_long.merge(df_depto.drop(columns=["departamento"]), on="depto_key", how="left")

print("Filas totales:", df_model.shape[0])
print("Filas sin match X:", df_model["prop_superior_mean"].isna().sum())

#Si hay deptos sin match, revisa nombres
unmatched=df_model["prop_superior_mean"].isna().sum()
if unmatched > 0:
    print(f"Filas sin match de X departamental: {unmatched}. Revisa normalización de nombres de departamento.")

# Nos quedamos con filas completas para el modelo

df_model=df_model.dropna(subset=["prop_superior_mean","estrato_pred_mean","rural_share"])

no_match = df_model[df_model["prop_superior_mean"].isna()]["depto_key"].value_counts()
print(no_match.head(30))
print("Keys en df_depto:", sorted(df_depto["depto_key"].unique())[:30])

df_model2 = df_model.dropna(subset=["prop_superior_mean","estrato_pred_mean","rural_share"]).copy()

print("df_model2 shape:", df_model2.shape)
print("Años únicos:", df_model2["anio"].nunique())
print("Deptos únicos:", df_model2["departamento"].nunique())

print("Departamentos incluidos en el modelo: ",sorted(df_model2["departamento"].unique()))

df_model2.to_csv(os.path.join(OUT_DIR,"df_model_panel_departamento.csv"), index=False)

#Modelos

# Modelo 1: FE por año (baseline)
m1=smf.ols(
    "tasa_desercion ~ prop_superior_mean + estrato_pred_mean + rural_share + C(anio)",
    data=df_model2
).fit(cov_type="HC3")

print(m1.summary())

#Modelo 2: FE por año + FE por departamento
#Como las X son constantes por depto, con C(departamento) pueden volverse colineales.

m2=smf.ols(
    formula="tasa_desercion ~ prop_superior_mean + estrato_pred_mean + rural_share + C(anio) + C(departamento)",
    data=df_model
).fit(cov_type="HC3")

# Guardar resúmenes
with open(os.path.join(OUT_DIR, "modelo_1_summary.txt"),"w",encoding="utf-8") as f:
    f.write(m1.summary().as_text())

with open(os.path.join(OUT_DIR, "modelo_2_summary.txt"),"w",encoding="utf-8") as f:
    f.write(m2.summary().as_text())

#Tabla compacta de coeficientes principales
def coef_table(model,name):
    params=model.params
    se=model.bse
    pval=model.pvalues
    out=pd.DataFrame({
        "coef":params,
        "se":se,
        "pval":pval
    })
    out["modelo"]=name
    return out.reset_index().rename(columns={"index":"termino"})

coef_df=pd.concat([coef_table(m1,"M1_FE_anio"), coef_table(m2,"M2_FE_anio_depto")],ignore_index=True)
coef_df.to_csv(os.path.join(TAB_DIR,"03_coeficientes_modelos.csv"),index=False)

#Diagnósticos mínimos

#Residuos (M1)
resid=m1.resid
fitted=m1.fittedvalues

plt.figure()
plt.hist(resid,bins=30,color="pink")
plt.title("Distribución de residuos (Modelo 1)")
plt.xlabel("Residuo")
plt.ylabel("Frecuencia")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "diag_01_hist_residuos_m1.png"), dpi=200)
plt.close()

plt.figure()
plt.scatter(fitted,resid,alpha=0.5,color="pink")
plt.axhline(0)
plt.title("Residuos vs Ajustados (Modelo 1)")
plt.xlabel("Valores ajustados")
plt.ylabel("Residuos")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "diag_02_residuos_vs_ajustados_m1.png"), dpi=200)
plt.close()

#Correlación simple entre X
Xcorr=df_model[["prop_superior_mean","estrato_pred_mean","rural_share"]].corr()
Xcorr.to_csv(os.path.join(TAB_DIR,"04_corr_X.csv"))

print("Listo. Revisa la carpeta output_model/ (tablas, figuras y summaries).")
