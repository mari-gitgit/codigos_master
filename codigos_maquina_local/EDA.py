import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(r"C:\Users\paper\Desktop\Master\df_master_municipal.csv")

# 1. Municipios por tipo de ruralidad
plt.figure()
df["tipo_ruralidad"].value_counts().plot(kind="bar",color="pink")
plt.xlabel("Tipo de ruralidad")
plt.ylabel("Número de municipios")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# 2. Estrato socioeconómico predominante
plt.figure()
df["estrato_predominante"].value_counts().sort_index().plot(kind="bar",color="pink")
plt.xlabel("Estrato predominante")
plt.ylabel("Número de municipios")
plt.tight_layout()
plt.show()

# 3. Escolaridad total
plt.figure()
df["escolaridad_total"].dropna().plot(kind="hist",bins=30,color="pink")
plt.xlabel("Escolaridad total")
plt.ylabel("Número de municipios")
plt.tight_layout()
plt.show()

# 4. Escolaridad vs estrato (boxplot)

df["esc_superior"] = (
    df["esc_tecnica_profesional"]
    + df["esc_tecnologica"]
    + df["esc_profesional"]
    + df["esc_especializacion"]
    + df["esc_maestria"]
    + df["esc_doctorado"]
)

niveles = [
    "esc_preescolar",
    "esc_basica_primaria",
    "esc_basica_secundaria",
    "esc_media_academica_clasica",
    "esc_media_tecnica",
    "esc_superior"
]

for col in niveles:
    df[f"prop_{col.replace('esc_', '')}"] = df[col] / df["escolaridad_total"]

plt.figure()
df.boxplot(column="prop_superior", by="estrato_predominante",color="hotpink")
plt.title("")
plt.suptitle("")
plt.xlabel("Estrato predominante")
plt.ylabel("Proporción")
plt.tight_layout()
plt.show()
