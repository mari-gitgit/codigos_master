import pandas as pd

archivo=r"C:\Users\paper\Documents\Deserción universidades\DCD-area-proypoblacion-dep-2020-2050-ActPostCOVID-19.xlsx"
hoja="Departamental_2020-2035"

#Leemos la hoja
raw=pd.read_excel(archivo,sheet_name=hoja,header=None)

#Encontrar la fila con los títulos
mask_header=(
    (raw.iloc[:,0]=="DP") &
    (raw.iloc[:,1]=="DPNOM") &
    (raw.iloc[:,2]=="AÑO")
)
header_idx=raw.index[mask_header][0]

#Construimos la tabla
tabla=raw.iloc[header_idx+1:,:].copy()
tabla.columns=raw.iloc[header_idx]

#Limpiamos, quitamos filas vacías
tabla=tabla.dropna(how="all")
tabla=tabla[tabla["AÑO"].notna()].reset_index(drop=True)

#Guardamos en CSV
salida=r"C:\Users\paper\Desktop\Master\proyección_poblacion.csv"
tabla.to_csv(salida,index=False,encoding="utf-8")
