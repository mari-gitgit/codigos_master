import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from utils import fig_bar,fig_hist,freq_table_EDA

df = pd.read_csv(r"C:\Users\paper\Desktop\Master\df_master_municipal.csv")

#Calidad de datos
#Dimensiones y duplicados
quality_summary={
    "filas":df.shape[0],
    "columnas":df.shape[1],
    "duplicados_codigo_dane":int(df["codigo_dane"].duplicated().sum()) if "codigo_dane" in df.columns else None
}
print("Calidad de los datos:")
print(quality_summary)

#Nulos
missing=pd.DataFrame({
    "columna":df.columns,
    "nulos": [int(df[c].isna().sum()) for c in df.columns],
    "pct_nulos":[float(df[c].isna().mean()) for c in df.columns],
}).sort_values("pct_nulos",ascending=False)

print("Valores Nulos:")
print(missing)

#Municipios sin info
educ_cols=[c for c in df.columns if c.startswith("esc_")]+(["escolaridad_total"] if "escolaridad_total" in df.columns else [])
if len(educ_cols)>0:
    df["educ_info_disp"]=(~df[educ_cols].isna().all(axis=1)).astype(int)
    sin_educ=df[df["educ_info_disp"]==0][["codigo_dane","departamento","municipio"]] if {"codigo_dane","departamento","municipio"}.issubset(df.columns) else df[df["educ_info_disp"]==0]
    print("Municipios sin información educativa: ")
    print(sin_educ)

#Top municipios por manzanas (para evidenciar escala)
print("Top municipios por número de manzanas:")
print(df.sort_values("n_manzanas_total", ascending=False)[
    ["departamento", "municipio", "n_manzanas_total"]
].head(10))

#Variables derivadas (composición educativa)
#Construir educación superior agregada
superior_parts=["esc_tecnica_profesional","esc_tecnologica","esc_profesional",
                  "esc_especializacion","esc_maestria","esc_doctorado"]

if all(col in df.columns for col in superior_parts):
    df["esc_superior"]=df[superior_parts].sum(axis=1)

#Construir proporciones (evitamos el sesgo por tamaño)
#Solo crea proporciones para columnas existentes
prop_base=[c for c in df.columns if c.startswith("esc_")]
if "escolaridad_total" in df.columns:
    #Evitamos división por 0 y por NaN
    denom=df["escolaridad_total"].replace({0:np.nan})
    for col in prop_base:
        df[f"prop_{col.replace('esc_','')}"]=df[col] / denom

#Guardamos el dataset para seguir con el EDA
df.to_csv("df_master_derived.csv",index=False)

#Distribuciones univariadas

#Distribución de municipios por tipo de ruralidad
if "tipo_ruralidad" in df.columns:
    fig_bar(df["tipo_ruralidad"],"Tipo de ruralidad","Número de municipios",
            "fig_5_ruralidad.png","pink")

tab_ruralidad = freq_table_EDA(df, "tipo_ruralidad")
tab_ruralidad.to_csv("frecuencias_ruralidad.csv",index=False)

#Estrato socioeconómico predominante
plt.figure()
df["estrato_predominante"].value_counts().sort_index().plot(kind="bar",color="pink")
plt.xlabel("Estrato predominante")
plt.ylabel("Número de municipios")
plt.tight_layout()
plt.savefig("fig_1_estrato_predominante.png")
plt.close()

tab_estrato=freq_table_EDA(df,"estrato_predominante")
tab_estrato.to_csv("frecuencias_estrato.csv", index=False)

#Escolaridad total por municipio
if "escolaridad_total" in df.columns:
    fig_hist(df["escolaridad_total"],"Escolaridad total (conteo agregado)","Número de municipios",
             "fig_2_escolaridad_total.png","pink")
#LIGHTSHOT
#Manzanas por municipio
if "n_manzanas_total" in df.columns:
    fig_hist(df["n_manzanas_total"],"Número de manzanas","Número de municipios",
             "fig_3_manzanas_total.png","pink")

#Población departamental
if "poblacion_departamental" in df.columns:
    fig_hist(df["poblacion_departamental"],"Población departamental (último año disponible)",
             "Número de municipios","fig_poblacion_departamental","pink")

#Top municipios por departamento
plt.figure()
df["departamento"].value_counts().head(10).plot(kind="bar",color="pink")
plt.xlabel("Departamento")
plt.ylabel("Número de municipios")
plt.xticks(rotation=45,ha="right")
plt.tight_layout()
plt.savefig("fig_top_departamentos.png",dpi=200)
plt.close()

tab_deptos = freq_table_EDA(df,"departamento")
tab_deptos.to_csv("frecuencias_departamento.csv", index=False)

#Relaciones bivariadas
#Escolaridad total vs Estrato (aclarar que es volumen, no logros académicos)
if {"escolaridad_total","estrato_predominante"}.issubset(df.columns):
    plt.figure()
    df.boxplot(column="escolaridad_total",by="estrato_predominante",color="pink")
    plt.suptitle("")
    plt.xlabel("Estrato predominante")
    plt.ylabel("Escolaridad total")
    plt.tight_layout()
    plt.savefig("fig_4_escolaridad.png")

#Proporción de educación superior vs estrato
if {"prop_superior","estrato_predominante"}.issubset(df.columns):
    plt.figure()
    df.boxplot(column="prop_superior",by="estrato_predominante",color="pink")
    plt.suptitle("")
    plt.xlabel("Estrato predominante")
    plt.ylabel("Proporción")
    plt.tight_layout()
    plt.savefig("fig_6_proporcion.png")
    plt.close()

#Ruralidad vs Estrato
if {"tipo_ruralidad","estrato_predominante"}.issubset(df.columns):
    ct=pd.crosstab(df["tipo_ruralidad"],df["estrato_predominante"],normalize="index")
    ct.to_csv("cross_tab_ruralidad_estrato.csv")

    #Gráfico
    ax=ct.plot(kind="bar",stacked=True,color=["pink","magenta","crimson"])
    ax.set_xlabel("Tipo de ruralidad")
    ax.set_ylabel("Proporción")
    plt.xticks(rotation=45,ha="right")
    plt.tight_layout()
    plt.savefig("fig_cross_tab_proporcion.png",dpi=200)
    plt.close()

#Correlaciones numéricas
num_cols=df.select_dtypes(include=["number"]).columns.tolist()
if len(num_cols)>1:
    corr=df[num_cols].corr(numeric_only=True)
    corr.to_csv("corr_numerica.csv")

