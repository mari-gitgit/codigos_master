import re
import numpy as np
import pandas as pd
from unidecode import unidecode
import matplotlib.pyplot as plt

def freq_table_EDA(df, col):
    tab = pd.DataFrame({
        "frecuencia": df[col].value_counts(dropna=False),
        "proporcion": df[col].value_counts(normalize=True, dropna=False)
    }).reset_index()

    tab = tab.rename(columns={"index": col})
    return tab

def normalize_col_name(col):
    try:
        val=float(col)
        if val.is_integer() and 1900<=val<=2100:
            return str(int(val))
    except:
        pass
    return col

def norm_text(s:str) -> str:
    """Normaliza texto: mayúsculas, sin tildes, sin signos, espacios limpios."""
    if s is None:
        return ""
    s=str(s).strip().upper()
    s=unidecode(s)
    s=re.sub(r"\s+", " ",s)
    s=s.replace(".","").replace(",","")
    return s

def norm_depto(s: str) -> str:
    """Normalización específica para nombres de departamento en Colombia."""
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unidecode(s)                 # quita tildes
    s = re.sub(r"\s+", " ", s)       # espacios dobles
    s = s.replace(".", "").replace(",", "")
    s = s.replace(" D C", " DC")     # arreglos comunes
    s = s.replace("D C", "DC")
    # normalizaciones comunes en Colombia
    s = s.replace("BOGOTA DC", "BOGOTA")
    s = s.replace("BOGOTA D C", "BOGOTA")
    s = s.replace("ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA", "SAN ANDRES")
    return s

def add_prop(df:pd.DataFrame, num_col:str, den_col:str, out_col:str) -> pd.DataFrame:
    """Crea una proporción num/den evitando división por 0."""
    df=df.copy()
    df[out_col]=df[num_col]/df[den_col].replace({0:np.nan})
    return df

def freq_table(df:pd.DataFrame, col:str) -> pd.DataFrame:
    """Tabla de frecuencias absoluta y relativa."""
    abs_counts=df[col].value_counts(dropna=False)
    rel_counts=df[col].value_counts(normalize=True,dropna=False)
    out=pd.DataFrame({"frecuencia":abs_counts,"proporcion":rel_counts})
    out.index.name=col
    return out.reset_index()

def save_freq_table(df:pd.DataFrame, col:str, path_out:str) -> pd.DataFrame:
    """Genera y guarda una tabla de frecuencias."""
    tab = freq_table(df,col)
    tab.to_csv(path_out,index=False)
    return tab

def fig_bar(series,xlabel,ylabel,filename,color_fig,rotation=45):
    """Generar y guardar gráficas de barras"""
    plt.figure()
    series.value_counts().plot(kind="bar",color=color_fig)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=rotation,ha="right")
    plt.tight_layout()
    plt.savefig(filename,dpi=200)
    plt.close()

def fig_hist(series,xlabel,ylabel,filename,color_fig,bins=45):
    """Generar y guardar histogramas"""
    plt.figure()
    series.dropna().plot(kind="hist",bins=bins,color=color_fig)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(filename,dpi=200)
    plt.close()

def coef_table(model,name):
    """Tabla compacta de coeficientes principales"""
    params=model.params
    se=model.bse
    pval=model.pvalues
    out=pd.DataFrame({
        "coef":params,
        "se":se,
        "pval":pval
    })
    out["modelo"]=name
    return out.reset_index().rename(columns={"index":"termino"})
