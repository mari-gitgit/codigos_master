import pandas as pd

#Configuramos inicialmente los nombres de archivos y hojas
path=r"C:\Users\paper\Documents\Deserción universidades\Servicios públicos por departamento.xlsx"
sheet="Output"
out_csv="servicios_publicos_por_departamento_limpio.csv"

#Cargamos el archivo
df=pd.read_excel(path,sheet_name=sheet)

#Se asume una estructura típica
col0,col1,col2,col3,col4=df.columns[:5]

#Detectar inicios de tabla por Área
area_rows=[
    i for i, v in df[col1].items()
    if isinstance(v,str) and v.strip().upper().startswith("AREA #")
]

records=[]

#Procesamos cada bloque
for k,start in enumerate(area_rows):
    end=area_rows[k+1] if k+1 < len(area_rows) else len(df)

    #Departamento se encuentra en la columna 2
    dept=df.at[start,col2]
    if not isinstance(dept,str) or not dept.strip():
        continue
    dept=dept.strip()

    #Quitamos tabla RESUMEN
    if dept.lower() == "resumen":
        continue

    #Buscamnos el encabezado real de la tabla
    header_idx=None
    is_resumen=False

    for r in range(start,min(start+15,end)):
        cell=df.at[r, col1]

        # Si aparece la palabra RESUMEN, descartamos todo el bloque
        if isinstance(cell,str) and cell.strip().upper() == "RESUMEN":
            is_resumen=True
            break

        v2=df.at[r,col2]
        v3=df.at[r,col3]

        if (
                isinstance(v2,str) and v2.strip().lower() == "casos"
                and isinstance(v3,str) and v3.strip() == "%"
        ):
            header_idx=r
            break

    #Saltamos los bloques de resumen
    if is_resumen or header_idx is None:
        continue

    #Nombre del servicio
    servicio=df.at[header_idx, col1]
    servicio=servicio.strip() if isinstance(servicio,str) else ""

    #Extraemos filas válidas
    VALID_RESPUESTAS={"SI","NO"}

    #Determinamos hasta dónde leer: parar en RESUMEN (o en otro AREA #)
    data_end=end
    for rr in range(header_idx+1,end):
        marker=df.at[rr,col1]
        if isinstance(marker,str):
            m=marker.strip().upper()
            if m == "RESUMEN" or m.startswith("AREA #"):
                data_end=rr
                break

    for r in range(header_idx+1,data_end):
        resp=df.at[r,col1]

        if not isinstance(resp,str):
            continue

        resp=resp.strip()

        if resp == "":
            continue
        if resp.lower() == "total":
            continue
        if resp.upper().startswith("AREA #"):
            continue
        if resp.upper() == "RESUMEN":
            break

        #Descartamos cuando la "respuesta" repite el nombre del servicio
        if resp.lower() == servicio.lower():
            continue

        if resp.upper() not in VALID_RESPUESTAS:
            continue

        casos=df.at[r, col2]
        pct=df.at[r, col3]

        if pd.isna(casos) and pd.isna(pct):
            continue

        records.append({
            "Departamento":dept,
            "Servicio":servicio,
            "Respuesta":resp.upper(),
            "Casos":casos,
            "Porcentaje":pct
        })

#Dataframe final
clean = pd.DataFrame(records)

#Convertir numéricos
clean["Casos"] = pd.to_numeric(clean["Casos"], errors="coerce")
clean["Porcentaje"] = pd.to_numeric(clean["Porcentaje"], errors="coerce")

#Exportamos
clean.to_csv(out_csv, index=False, encoding="utf-8-sig")
