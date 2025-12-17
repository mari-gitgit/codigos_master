import pandas as pd

archivo=r"C:\Users\paper\Documents\Deserción universidades\anex-PM-TotalNacional-2024.xlsx"
hoja="IP_Sexo Act.Met."

#Leer hoja
raw=pd.read_excel(archivo,sheet_name=hoja,header=None)

#Encontrar la fila donde comienza exactamente
fila_header=raw.index[
    raw.iloc[:,0].astype(str).str.strip().eq("Grandes dominios")
][0]

#Tomar las cinco primeras columnas
df=raw.iloc[fila_header+2:,0:5].copy()

#Cortar en la primera fila totalmente vacía (fin de la tabla)
if df.isna().all(axis=1).any():
    fila_fin=df.index[df.isna().all(axis=1)][0]
    df=df.loc[:fila_fin-1]

#Poner nombres de columnas
df.columns=["Área","2023_Hombre","2023_Mujer","2024_Hombre","2024_Mujer"]
df=df.reset_index(drop=True)

#Encontrar las filas de ciudades capitales y ciudades con área metropolitana
idx_capitales=df.index[df["Área"]=="Ciudades capitales"][0]
idx_am=df.index[df["Área"]=="Ciudades con Área Metropolitana"][0]

#Separamos
grandes_dominios_rural_sexo=df.iloc[:idx_capitales,:].reset_index(drop=True)
ciudades_capitales_sexo=df.iloc[idx_capitales+1:idx_am,:].reset_index(drop=True)

#Guardamos en CSV
grandes_dominios_rural_sexo.to_csv(
    r"C:\Users\paper\Desktop\Master\IP_Sexo_grandes_dominios.csv",
    index=False,
    encoding="utf-8",
)

ciudades_capitales_sexo.to_csv(
    r"C:\Users\paper\Desktop\Master\IP_Sexo_ciudades_capitales.csv",
    index=False,
    encoding="utf-8"
)
