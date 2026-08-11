import pandas as pd
from config import MESES_COLUMNAS, MESES_UI, CONFIG_INDICADORES

def sugerir_mes_final(df):
    """Detecta el último mes que contiene al menos un dato numérico."""
    for mes in reversed(MESES_COLUMNAS):
        if pd.to_numeric(df[mes], errors="coerce").notna().any():
            return MESES_UI[MESES_COLUMNAS.index(mes)]
    return MESES_UI[0]

def obtener_meses_periodo(mes_inicio_ui, mes_fin_ui):
    idx_inicio = MESES_UI.index(mes_inicio_ui)
    idx_fin = MESES_UI.index(mes_fin_ui)
    if idx_inicio > idx_fin:
        raise ValueError("El mes inicial no puede ser posterior al mes final.")
    return MESES_COLUMNAS[idx_inicio:idx_fin + 1]

def _normalizar_tipo(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return "vacío"
    return str(valor).strip()

def procesar_datos_por_cite(df, cite, anio, mes_inicio_ui, mes_fin_ui):
    """Construye la vista y los valores que alimentarán la ficha."""
    meses_rango = obtener_meses_periodo(mes_inicio_ui, mes_fin_ui)
    trabajo = df.copy()
    trabajo["tipo"] = trabajo["tipo"].apply(_normalizar_tipo)
    df_filtrado = trabajo[trabajo["cite_ut"].astype(str).str.strip() == str(cite).strip()].copy()

    if df_filtrado.empty:
        raise ValueError(f"No se encontraron datos para '{cite}'.")

    resultados = []
    for id_ind, config in CONFIG_INDICADORES.items():
        indicador = config["nombre"]
        for variable, var_config in config["variables"].items():
            tipo_esperado = var_config["tipo_df"]
            df_var = df_filtrado[
                (df_filtrado["Indicador"].astype(str).str.strip() == indicador)
                & (df_filtrado["tipo"] == tipo_esperado)
            ]

            if len(df_var) != 1:
                raise ValueError(
                    f"Se esperaba un registro para {cite} - {indicador} ({tipo_esperado}) "
                    f"y se encontraron {len(df_var)}."
                )

            origen = df_var.iloc[0]
            fila = {
                "Indicador": indicador,
                "Variable": variable,
                "Tipo": tipo_esperado,
            }

            suma_periodo = 0.0
            hay_dato_numerico = False

            for mes in MESES_COLUMNAS:
                if mes not in meses_rango:
                    fila[mes] = "-"
                    continue

                val = origen[mes]
                if pd.isna(val) or str(val).strip() == "":
                    fila[mes] = ""
                elif str(val).strip() == "-":
                    fila[mes] = "-"
                else:
                    num = pd.to_numeric(val, errors="coerce")
                    if pd.isna(num):
                        raise ValueError(
                            f"Valor no numérico en {cite} - {indicador} - {mes}: {val}"
                        )
                    num = float(num)
                    fila[mes] = int(num) if num.is_integer() else num
                    suma_periodo += num
                    hay_dato_numerico = True

            fila["Suma_Periodo"] = suma_periodo if hay_dato_numerico else None
            fila["Total_Original"] = origen["Total"]
            resultados.append(fila)

    df_res = pd.DataFrame(resultados)
    return calcular_valor_alcanzado(df_res)

def calcular_valor_alcanzado(df_res):
    alertas = []
    df_res = df_res.copy()
    df_res["Valor Alcanzado"] = ""

    for id_ind, config in CONFIG_INDICADORES.items():
        mask_ind = df_res["Indicador"] == config["nombre"]

        if config["tipo_calculo"] == "suma":
            idx = df_res.index[mask_ind][0]
            suma = df_res.at[idx, "Suma_Periodo"]
            df_res.at[idx, "Valor Alcanzado"] = "" if suma is None else (
                int(suma) if float(suma).is_integer() else suma
            )

        elif config["tipo_calculo"] == "porcentaje":
            idx_num = df_res.index[mask_ind & (df_res["Tipo"] == "Numerador")]
            idx_den = df_res.index[mask_ind & (df_res["Tipo"] == "Denominador")]
            if len(idx_num) != 1 or len(idx_den) != 1:
                raise ValueError(f"No se pudo identificar numerador/denominador del Indicador {id_ind}.")

            num = df_res.at[idx_num[0], "Suma_Periodo"]
            den = df_res.at[idx_den[0], "Suma_Periodo"]

            if den is None or den == 0:
                df_res.at[idx_num[0], "Valor Alcanzado"] = "-"
                alertas.append(
                    f"El Indicador {id_ind} no puede calcularse porque el denominador "
                    "del periodo es cero o no tiene datos."
                )
            elif num is None:
                df_res.at[idx_num[0], "Valor Alcanzado"] = "-"
                alertas.append(
                    f"El Indicador {id_ind} no puede calcularse porque el numerador no tiene datos."
                )
            else:
                df_res.at[idx_num[0], "Valor Alcanzado"] = float(num) / float(den)

    columnas = ["Indicador", "Variable"] + MESES_COLUMNAS + ["Total_Original", "Valor Alcanzado"]
    return df_res[columnas], alertas
