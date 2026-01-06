import camelot
import pandas as pd

file_path=r"C:\Users\paper\Documents\Deserción universidades\Definicion Categorías de Ruralidad.pdf"

tables=camelot.read_pdf(file_path, pages="18-19", flavor='lattice')

def procesar_tabla(t, tipo_ruralidad):
    df=t.df.copy().reset_index(drop=True)
    n_cols=df.shape[1]
    partes=[]

    if n_cols >= 6:
        left=df.iloc[1:, 0:3].copy()
        right=df.iloc[1:, 3:6].copy()

        left.columns=["Departamento","Municipio","Codigo_DANE"]
        right.columns=["Departamento","Municipio","Codigo_DANE"]

        left["Departamento"]=left["Departamento"].replace("", pd.NA)

        #Rellenamos dentro de la tabla izquierda
        left["Departamento"]=left["Departamento"].ffill()

        right["Departamento"]=right["Departamento"].replace("", pd.NA)

        partes=[left, right]

    elif n_cols >= 3:
        sub=df.iloc[1:, 0:3].copy()
        sub.columns=["Departamento","Municipio","Codigo_DANE"]
        sub["Departamento"]=sub["Departamento"].replace("", pd.NA)
        partes=[sub]

    else:
        print("Tabla con columnas inesperadas:", n_cols)
        return pd.DataFrame()

    out=pd.concat(partes,ignore_index=True)

    # Limpiar y rellenar Departamento nuevamente
    out["Departamento"]=out["Departamento"].astype("string")  # StringDtype, conserva <NA>
    out.loc[out["Departamento"].str.strip()=="", "Departamento"] = pd.NA
    out["Departamento"]=out["Departamento"].ffill()

    # Limpiar filas vacías de municipio
    out=out.dropna(subset=["Municipio"])
    out=out[out["Municipio"].str.strip() != ""]
    out=out[out["Municipio"].str.upper() != "MUNICIPIO"]

    out["Tipo_ruralidad"]=tipo_ruralidad
    return out

#Procesamos tablas
dfs_ciudades=[procesar_tabla(t,"Ciudades y aglomeraciones") for t in tables]
ciudades = pd.concat(dfs_ciudades, ignore_index=True)

#Repetimos para los demás tipos
tables_intermedio=camelot.read_pdf(file_path, pages="20-23", flavor='lattice')
intermedio=pd.concat([procesar_tabla(t,"Intermedio") for t in tables_intermedio],ignore_index=True)

tables_rural=camelot.read_pdf(file_path, pages="24-28", flavor='lattice')
rural=pd.concat([procesar_tabla(t,"Rural") for t in tables_rural],ignore_index=True)

tables_rural_d=camelot.read_pdf(file_path, pages="29-32", flavor='lattice')
rural_disperso=pd.concat([procesar_tabla(t,"Rural Disperso") for t in tables_rural_d],ignore_index=True)

#Se une todo
full=pd.concat([ciudades,intermedio,rural,rural_disperso],ignore_index=True)

full["Departamento"]=full["Departamento"].astype("string")
full.loc[full["Departamento"].str.strip()=="", "Departamento"] = pd.NA
full["Departamento"]=full["Departamento"].ffill()

#Limpiar saltos de línea en municipio y departamento
for col in ["Departamento","Municipio"]:
    full[col]=(
        full[col]
        .astype("string")
        .str.replace("\n", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

#Guardar en CSV
full.to_csv("tipos_ruralidad",index=False,encoding="utf-8")
