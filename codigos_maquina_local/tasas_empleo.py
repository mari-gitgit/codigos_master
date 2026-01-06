import pandas as pd
import numpy as np
from collections import defaultdict

ruta=r"C:\Users\paper\Documents\Deserción universidades\anex-GEIHDepartamentos-2024.xls"

#Creamos función para leer las hojas que necesitamos y guardar cada archivo
def procesar_hoja(ruta,hoja,origen):
    raw = pd.read_excel(ruta,sheet_name=hoja,header=None)

    tablas=[]
    n=raw.shape[0]

    #Detectamos filas donde hay <Departamento> seguido de una fila 'Concepto'
    dept_starts=[]
    for i in range(n-1):
        val=raw.iloc[i,0]
        next_val=raw.iloc[i+1,0]

        if (
            pd.notna(val)
            and isinstance(val,str)
            and val.strip() != ""
            and isinstance(next_val,str)
            and next_val.strip().lower()=="concepto"
        ):
            dept_starts.append(i)

    if not dept_starts:
        print(f"[AVISO] No se encontraron bloques Departamento/Concepto en la hoja {hoja}")
        return pd.DataFrame()

    for idx,start in enumerate(dept_starts):
        departamento=str(raw.iloc[start,0]).strip()
        header_row=start+1

        #Definimos hasta dónde llegan los datos de este departamento
        if idx<len(dept_starts)-1:
            end=dept_starts[idx+1]  # hasta antes del siguiente departamento
        else:
            end=n  # hasta el final de la hoja

        #Los datos comienzan 2 filas debajo del header
        data_start=header_row+2

        bloque=raw.iloc[data_start:end,:].copy()
        if bloque.empty:
            continue

        #Encabezados de columnas
        header=raw.iloc[header_row, :]
        bloque.columns=header

        #Quitamos filas 100% vacías
        bloque=bloque.dropna(how="all")
        bloque=bloque.loc[:,bloque.notna().any(axis=0)]

        #Limpiamos nombres de columnas y los hacemos únicos
        cols=[str(c).strip() for c in bloque.columns]
        new_cols=[]
        seen={}
        for c in cols:
            if c in seen:
                seen[c]+=1
                new_cols.append(f"{c}_{seen[c]}")
            else:
                seen[c]=0
                new_cols.append(c)
        bloque.columns=new_cols

        #Añadimos contexto
        bloque["Departamento"]=departamento
        bloque["Origen"]=origen

        tablas.append(bloque)

    if tablas:
        return pd.concat(tablas, ignore_index=True)
    else:
        return pd.DataFrame()

#Procesamos las 4 hojas
config_hojas=[
    ("Departamento anual Cabeceras", "Cabeceras"),
    ("Departamento anual CentrosP", "CentrosP"),
    ("Departamentos anual mujeres", "Mujeres"),
    ("Departamentos anual hombres", "Hombres"),
]

dfs=[]

for nombre_hoja,origen in config_hojas:
    df_hoja=procesar_hoja(ruta,nombre_hoja,origen)
    print(nombre_hoja,df_hoja.shape)
    if not df_hoja.empty:
        dfs.append(df_hoja)

if dfs:
    df_todo=pd.concat(dfs, ignore_index=True)
    df_todo=df_todo.loc[:, df_todo.notna().any(axis=0)]

    print(df_todo.head(10))
    print(df_todo["Origen"].value_counts())
    print(df_todo["Departamento"].unique()[:10])

df=df_todo.copy()

#Normalizamos los nombres de las columnas
def normalize_col_name(col):
    try:
        val=float(col)
        if val.is_integer() and 1900<=val<=2100:
            return str(int(val))
    except:
        pass
    return col


#Mapeamos columna_original → columna_normalizada
normalized={col:normalize_col_name(col) for col in df.columns}

groups=defaultdict(list)

for original,norm in normalized.items():
    groups[norm].append(original)

#Creamos df nuevo con columnas unificadas correctamente
df_unificado=pd.DataFrame(index=df.index)

for norm_name,cols in groups.items():
    if len(cols)==1:
        df_unificado[norm_name]=df[cols[0]]
    else:
        #Unimos columnas duplicadas: tomar primer valor no nulo por fila
        combinado=df[cols].bfill(axis=1).iloc[:,0]
        df_unificado[norm_name]=combinado

#Reemplazamos df_todo por el unificado
df_todo=df_unificado

#Reemplazamos puntos "." por NaN en todas las columnas numéricas
df_todo=df_todo.replace(".", np.nan)

#Identificamos columnas de años
year_cols=[c for c in df_todo.columns if str(c).isdigit()]

#Eliminamos filas que son "Notas"
mask_notas=(
    df_todo["Concepto"]
    .astype(str)
    .str.strip()
    .str.lower()
    .str.startswith("nota")
)

df_todo=df_todo[~mask_notas].copy()

#Eliminamos filas totalmente vacías en los años
mask_all_years_null=df_todo[year_cols].isna().all(axis=1)

#También eliminamos filas donde Concepto es nulo o vacío
mask_concepto_vacio=df_todo["Concepto"].isna()|(
    df_todo["Concepto"].astype(str).str.strip()==""
)

# Fila basura
mask_basura=mask_all_years_null|mask_concepto_vacio

df_todo=df_todo[~mask_basura].copy()

#Reseteamos índice
df_todo=df_todo.reset_index(drop=True)

df_todo.to_csv(
    r"C:\Users\paper\Desktop\Master\Tasas_Empleo_Departamentos_LIMPIO.csv",
    index=False,
    encoding="utf-8-sig"
)
