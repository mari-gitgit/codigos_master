import pandas as pd

archivo=r"C:\Users\paper\Documents\Deserción universidades\anex-PM-TotalNacional-2024.xlsx"
hoja="Pobreza Monetaria Act.Met."

#Leemos la hoja completa
raw=pd.read_excel(archivo,sheet_name=hoja,header=None)

#Encontrar la fila donde aparece 2012
filas_2012=raw.index[(raw==2012).any(axis=1)].tolist()

if len(filas_2012)<1:
    raise ValueError("No se encontró ninguna fila con 2012 en la hoja.")

fila_header_1=filas_2012[0]

#Si hay otra tabla, la usamos como límite
if len(filas_2012)>=2:
    fila_header_2=filas_2012[1]
    raw_pct=raw.iloc[fila_header_1:fila_header_2,:]
else:
    raw_pct=raw.iloc[fila_header_1:,:]

#Construir la tabla correspondiente
columnas=raw_pct.iloc[0,:]
tabla=raw_pct.iloc[1:,:].reset_index(drop=True)
tabla.columns=columnas

#Eliminar columnas vacías
tabla=tabla.dropna(axis=1,how='all')

#Renombramos la primera columna por algo legible
cols=list(tabla.columns)
cols[0]="Área"
tabla.columns=cols

#Encontramos los índices de ciudades capitales y áreas metropolitanas
idx_cap=tabla.index[
    tabla["Área"].astype(str).str.contains("Ciudades capitales",case=False,na=False)
][0]

idx_am=tabla.index[
    tabla["Área"].astype(str).str.contains("Ciudades con Área Metropolitana",case=False,na=False)
][0]

#Separamos
grandes_dominios_ruralidad=tabla.iloc[:idx_cap,:].reset_index(drop=True)
ciudades_capitales=tabla.iloc[idx_cap+1:idx_am,:].reset_index(drop=True)

#Guardamos en CSV
grandes_dominios_ruralidad.to_csv(
    r"C:\Users\paper\Desktop\Master\pobreza_grandes_dominios_pct.csv",
    index=False,
    encoding="utf-8"
)

ciudades_capitales.to_csv(
    r"C:\Users\paper\Desktop\Master\ciudades_capitales_pobreza.csv",
    index=False,
    encoding="utf-8"
)
