import requests
import pandas as pd

base_url = "https://ags.esri.co/arcgis/rest/services/LivingAtlas/Estrato_predominante_por_manzana_2018/MapServer/0/query"

page_size = 2000     # máximo por request
offset = 0
all_rows = []

while True:
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "json",
        "resultOffset": offset,
        "resultRecordCount": page_size
    }

    print(f"Descargando desde offset {offset} ...")
    r = requests.get(base_url, params=params)
    r.raise_for_status()
    js = r.json()

    features = js.get("features", [])
    if not features:
        break

    # convertir features a filas (solo atributos)
    for ftr in features:
        attrs = ftr.get("attributes", {})
        all_rows.append(attrs)

    # si devolvió menos que page_size, ya no hay más
    if len(features) < page_size:
        break

    offset += page_size

print(f"Total de filas descargadas: {len(all_rows)}")

df = pd.DataFrame(all_rows)
print(df.head())
print(df.tail())
print(df.columns)

col_depto="DEPTO"
col_mnpio="MPIO"
col_estrato="ESTRATO_PREDOMINANTE_INT"

grouped=(
    df
    .groupby([col_depto,col_mnpio,col_estrato])
    .size()
    .reset_index(name="n_manzanas")
)

print(grouped.head())

grouped.to_csv("manzanas_estrato_por_municipio.csv",index=False,encoding="utf-8")
