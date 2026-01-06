import pandas as pd
import numpy as np
import re

# Ruta del archivo original
path=r"C:\Users\paper\Documents\Deserción universidades\Escolaridad por municipio.xlsx"

df=pd.read_excel(path,sheet_name="Output")

#Detectar la columna que contiene los nombres DEPARTAMENTO_MUNICIPIO
dept_muni_col=[c for c in df.columns if isinstance(c, str) and "_" in c][0]

#Obtener el primer dept/municipio desde el nombre de columna
dept0,muni0=dept_muni_col.split("_",1)

#Detectar bloques por municipio y encabezados de tablas
blocks=[]
current_dept,current_muni=dept0,muni0

for idx,row in df.iterrows():
    #Si aparece un nombre tipo ANTIOQUIA_MEDELLIN → nuevo municipio
    cell=row[dept_muni_col]
    if isinstance(cell,str) and re.match(r'^[A-Za-zÁÉÍÓÚÜÑ]+_[A-Za-zÁÉÍÓÚÜÑ ]+',cell):
        current_dept,current_muni=cell.split("_",1)

    # Detectar el encabezado de "Tipo de estudios que cursó"
    if isinstance(row['AREA # 05001'],str) and row['AREA # 05001'].strip()=="Tipo de estudios que cursó":
        blocks.append((idx,current_dept,current_muni))

#Convertir todo a formato largo
records=[]
nrows=len(df)

for b_idx,(header_idx,dept,muni) in enumerate(blocks):
    age_row=header_idx+1
    end=blocks[b_idx+1][0] if b_idx+1 < len(blocks) else nrows

    #Mapeo de columnas → etiqueta de grupo de edad
    age_labels={}
    for col in df.columns:
        if age_row<nrows:
            val=df.at[age_row,col]
        else:
            val=np.nan
        if isinstance(val,str) and val.strip() != "":
            label=val.strip()

            #Excluir la columna "Total" como grupo_edad
            if label.lower() == "total":
                continue

            age_labels[col]=label

    #Recorrer filas de tipos de estudio
    for r in range(age_row+1,end):
        tipo=df.at[r,'AREA # 05001']
        if not isinstance(tipo,str) or tipo.strip() == "":
            continue

        tipo=tipo.strip()

        #Saltar tipos que no necesitamos
        if (
            tipo=="Total" or
            tipo.startswith("No Aplica") or
            tipo.startswith("AREA #")
        ):
            continue

        for col,label in age_labels.items():
            value=df.at[r, col]

            #"-" → NaN
            if isinstance(value,str) and value.strip() == "-":
                value=np.nan

            #Convertir a numérico
            if isinstance(value,str):
                try:
                    value_num=float(value.replace(",",""))
                except:
                    value_num=np.nan
            else:
                value_num=value

            #Redondear al entero más cercano
            if pd.notna(value_num):
                value_num=round(value_num)

            records.append({
                "Departamento":dept,
                "Municipio":muni,
                "tipo_estudio":tipo,
                "grupo_edad":label,
                "valor":value_num
            })

#Dataframe final en formato largo
tidy=pd.DataFrame.from_records(records)

#Exportamos a csv
output_file="escolaridad_municipios_tidy.csv"
tidy.to_csv(output_file,index=False)

print(tidy.head())
