import io
import os
import re
import zipfile
import unicodedata
import openpyxl

from config import TEMPLATE_PATH, CONFIG_INDICADORES, MAPEO_COLUMNAS, CELDA_TITULO, MESES_COLUMNAS
from data_processor import procesar_datos_por_cite

def normalizar_nombre_archivo(nombre):
    texto = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode("ascii")
    texto = texto.replace(" ", "_")
    texto = re.sub(r"[^A-Za-z0-9_-]", "_", texto)
    return re.sub(r"_+", "_", texto).strip("_")

def _valor_excel(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor
    return valor

def generar_excel_bytes(df, cite, anio, mes_inicio_ui, mes_fin_ui):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(
            f"No se encontró la plantilla oficial: {TEMPLATE_PATH}. "
            "Cree la carpeta templates y coloque allí plantilla_gdr.xlsx."
        )

    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    ws = wb.active
    cite_mostrar = "NACIONAL" if cite == "0NACIONAL" else str(cite)

    ws[CELDA_TITULO] = (
        f"FICHA TÉCNICA DE INDICADORES {anio} - {cite_mostrar.upper()}\n"
        f"(PERIODO {mes_inicio_ui.upper()} - {mes_fin_ui.upper()} {anio})"
    )

    df_res, _ = procesar_datos_por_cite(
        df, cite, anio, mes_inicio_ui, mes_fin_ui
    )

    for id_ind, config in CONFIG_INDICADORES.items():
        for variable, var_config in config["variables"].items():
            coincidencia = df_res[
                (df_res["Indicador"] == config["nombre"])
                & (df_res["Variable"] == variable)
            ]
            if len(coincidencia) != 1:
                raise ValueError(
                    f"No se pudo identificar de forma única {config['nombre']} - {variable}."
                )

            fila_datos = coincidencia.iloc[0]
            fila_excel = var_config["fila"]

            for mes_col in MESES_COLUMNAS:
                celda = ws.cell(row=fila_excel, column=MAPEO_COLUMNAS[mes_col])
                celda.value = _valor_excel(fila_datos[mes_col])

        # El resultado se escribe una sola vez por indicador.
        fila_resultado = config["celda_resultado"]["fila"]
        col_resultado = config["celda_resultado"]["col"]

        if config["tipo_calculo"] == "porcentaje":
            fila_fuente = df_res[
                (df_res["Indicador"] == config["nombre"])
                & (df_res["Variable"] == "Número de encuestas respondidas")
            ].iloc[0]
            resultado = fila_fuente["Valor Alcanzado"]
            celda = ws.cell(row=fila_resultado, column=col_resultado)
            if resultado == "-":
                celda.value = "-"
            elif resultado == "" or resultado is None:
                celda.value = None
            else:
                celda.value = float(resultado)
                celda.number_format = "0.00%"
        else:
            fila_fuente = df_res[df_res["Indicador"] == config["nombre"]].iloc[0]
            resultado = fila_fuente["Valor Alcanzado"]
            ws.cell(row=fila_resultado, column=col_resultado).value = (
                None if resultado == "" else resultado
            )

    output = io.BytesIO()
    wb.save(output)
    wb.close()
    output.seek(0)
    return output.getvalue()

def generar_zip_todas_las_fichas(df, anio, mes_inicio_ui, mes_fin_ui, incluir_nacional):
    cites = [str(c).strip() for c in df["cite_ut"].dropna().unique()]
    zip_buffer = io.BytesIO()
    mes_ini = mes_inicio_ui[:3].upper()
    mes_fin = mes_fin_ui[:3].upper()
    fichas_generadas = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for cite in cites:
            if cite == "0NACIONAL" and not incluir_nacional:
                continue
            cite_nombre = "NACIONAL" if cite == "0NACIONAL" else cite
            nombre = (
                f"GDR_{normalizar_nombre_archivo(cite_nombre).upper()}_"
                f"{anio}_{mes_ini}_{mes_fin}.xlsx"
            )
            zf.writestr(
                nombre,
                generar_excel_bytes(df, cite, anio, mes_inicio_ui, mes_fin_ui),
            )
            fichas_generadas += 1

    zip_buffer.seek(0)
    return zip_buffer.getvalue(), fichas_generadas
