import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "plantilla_gdr.xlsx")

# La plantilla real contiene título y periodo en la celda combinada cuyo origen es B2.
CELDA_TITULO = "B2"

MESES_UI = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

MESES_COLUMNAS = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Set", "Oct", "Nov", "Dic"
]

MAPEO_COLUMNAS = {
    "Ene": 7, "Feb": 8, "Mar": 9, "Abr": 10, "May": 11, "Jun": 12,
    "Jul": 13, "Ago": 14, "Set": 15, "Oct": 16, "Nov": 17, "Dic": 18
}

COLUMNA_VALOR_ALCANZADO = 19  # S

CONFIG_INDICADORES = {
    1: {
        "nombre": "Indicador 1",
        "variables": {
            "Número de clientes": {"fila": 7, "rol": "unico", "tipo_df": "vacío"}
        },
        "tipo_calculo": "suma",
        "celda_resultado": {"fila": 7, "col": COLUMNA_VALOR_ALCANZADO},
    },
    2: {
        "nombre": "Indicador 2",
        "variables": {
            "Número de servicios": {"fila": 8, "rol": "unico", "tipo_df": "vacío"}
        },
        "tipo_calculo": "suma",
        "celda_resultado": {"fila": 8, "col": COLUMNA_VALOR_ALCANZADO},
    },
    3: {
        "nombre": "Indicador 3",
        "variables": {
            "Número de encuestas respondidas": {
                "fila": 9, "rol": "numerador", "tipo_df": "Numerador"
            },
            "Número de encuestas enviadas": {
                "fila": 10, "rol": "denominador", "tipo_df": "Denominador"
            },
        },
        "tipo_calculo": "porcentaje",
        "celda_resultado": {"fila": 9, "col": COLUMNA_VALOR_ALCANZADO},
    },
}

COLUMNAS_REQUERIDAS = [
    "Indicador", "cite_ut", "tipo",
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Set", "Oct", "Nov", "Dic",
    "Total", "%"
]
