import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "plantilla_gdr.xlsx")
METAS_PATH = os.path.join(DATA_DIR, "metas_gdr.xlsx")

CELDA_TITULO = "B2"
HOJA_GDR = "GDR"
HOJA_UP_INDICADOR_1 = "UP INDICADOR 1"
FILA_INICIO_UP = 4

MESES_UI = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

MESES_COLUMNAS = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Set", "Oct", "Nov", "Dic"
]

# Nueva plantilla: G = meta; H:S = meses; T = alcanzado; U = avance.
MAPEO_COLUMNAS = {
    "Ene": 8, "Feb": 9, "Mar": 10, "Abr": 11, "May": 12, "Jun": 13,
    "Jul": 14, "Ago": 15, "Set": 16, "Oct": 17, "Nov": 18, "Dic": 19
}

COLUMNA_META = 7       # G
COLUMNA_VALOR_ALCANZADO = 20  # T
COLUMNA_AVANCE = 21    # U

CONFIG_INDICADORES = {
    1: {
        "nombre": "Indicador 1",
        "columna_meta": "Meta Indicador 1",
        "variables": {
            "Número de clientes": {"fila": 7, "rol": "unico", "tipo_df": "vacío"}
        },
        "tipo_calculo": "suma",
        "celda_meta": {"fila": 7, "col": COLUMNA_META},
        "celda_resultado": {"fila": 7, "col": COLUMNA_VALOR_ALCANZADO},
        "celda_avance": {"fila": 7, "col": COLUMNA_AVANCE},
    },
    2: {
        "nombre": "Indicador 2",
        "columna_meta": "Meta Indicador 2",
        "variables": {
            "Número de servicios": {"fila": 8, "rol": "unico", "tipo_df": "vacío"}
        },
        "tipo_calculo": "suma",
        "celda_meta": {"fila": 8, "col": COLUMNA_META},
        "celda_resultado": {"fila": 8, "col": COLUMNA_VALOR_ALCANZADO},
        "celda_avance": {"fila": 8, "col": COLUMNA_AVANCE},
    },
    3: {
        "nombre": "Indicador 3",
        "columna_meta": "Meta Indicador 3",
        "variables": {
            "Número de encuestas respondidas": {
                "fila": 9, "rol": "numerador", "tipo_df": "Numerador"
            },
            "Número de encuestas enviadas": {
                "fila": 10, "rol": "denominador", "tipo_df": "Denominador"
            },
        },
        "tipo_calculo": "porcentaje",
        "celda_meta": {"fila": 9, "col": COLUMNA_META},
        "celda_resultado": {"fila": 9, "col": COLUMNA_VALOR_ALCANZADO},
        # El Indicador 3 NO muestra porcentaje de avance. U9:U10 queda vacío/plomo.
        "celda_avance": None,
    },
}

COLUMNAS_REQUERIDAS = [
    "Indicador", "cite_ut", "tipo",
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Set", "Oct", "Nov", "Dic",
    "Total", "%"
]

COLUMNAS_METAS_REQUERIDAS = [
    "CITE", "Meta Indicador 1", "Meta Indicador 2", "Meta Indicador 3"
]

COLUMNAS_UP_REQUERIDAS = [
    "CITE", "N°", "RUC/DNI/CE/OTROS",
    "RAZON SOCIAL / APELLIDOS Y NOMBRES", "CATEGORIA"
]
