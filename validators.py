import pandas as pd
from config import (
    COLUMNAS_REQUERIDAS,
    COLUMNAS_METAS_REQUERIDAS,
    COLUMNAS_UP_REQUERIDAS,
    MESES_COLUMNAS,
)


def _normalizar_tipo(serie):
    return (
        serie.fillna("vacío")
        .astype(str)
        .str.strip()
        .replace({"": "vacío", "nan": "vacío", "NaN": "vacío"})
    )


def validar_datos_entrada(df):
    """Valida estructura y consistencia del consolidado sin ocultar errores críticos."""
    advertencias = []

    columnas_faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if columnas_faltantes:
        return False, f"Faltan las columnas: {', '.join(columnas_faltantes)}", []

    df["Indicador"] = df["Indicador"].astype(str).str.strip()
    df["cite_ut"] = df["cite_ut"].astype(str).str.strip()
    df["tipo"] = _normalizar_tipo(df["tipo"])

    if (df["cite_ut"] == "").any():
        return False, "Existen registros sin CITE/UT.", []

    duplicados = df.duplicated(subset=["Indicador", "cite_ut", "tipo"], keep=False)
    if duplicados.any():
        ejemplos = df.loc[duplicados, ["Indicador", "cite_ut", "tipo"]].drop_duplicates()
        muestra = "; ".join(
            f"{r.cite_ut} - {r.Indicador} ({r.tipo})" for r in ejemplos.itertuples()
        )
        return False, f"Hay combinaciones duplicadas Indicador-CITE-Tipo: {muestra}", []

    errores_estructura = []
    for cite in df["cite_ut"].dropna().unique():
        d = df[df["cite_ut"] == cite]
        requeridos = [
            ("Indicador 1", "vacío"),
            ("Indicador 2", "vacío"),
            ("Indicador 3", "Numerador"),
            ("Indicador 3", "Denominador"),
        ]
        for indicador, tipo in requeridos:
            existe = ((d["Indicador"] == indicador) & (d["tipo"] == tipo)).any()
            if not existe:
                etiqueta = indicador if tipo == "vacío" else f"{indicador} ({tipo})"
                errores_estructura.append(f"{cite}: falta {etiqueta}")

    if errores_estructura:
        return False, "El archivo está incompleto. " + " | ".join(errores_estructura[:12]), []

    for _, row in df.iterrows():
        suma = 0.0
        hay_numeros = False
        for mes in MESES_COLUMNAS:
            val = row[mes]
            if pd.isna(val) or str(val).strip() in ("", "-"):
                continue
            num = pd.to_numeric(val, errors="coerce")
            if pd.isna(num):
                advertencias.append(
                    f"Valor no numérico en {row['cite_ut']} - {row['Indicador']} - {mes}: {val}"
                )
            else:
                suma += float(num)
                hay_numeros = True

        total = pd.to_numeric(row["Total"], errors="coerce")
        if hay_numeros and pd.notna(total) and abs(suma - float(total)) > 0.01:
            etiqueta = row["Indicador"] if row["tipo"] == "vacío" else f"{row['Indicador']} ({row['tipo']})"
            advertencias.append(
                f"Inconsistencia en {row['cite_ut']} - {etiqueta}: "
                f"suma mensual {suma:g} vs Total {float(total):g}."
            )

    return True, "Archivo validado correctamente.", advertencias


def validar_metas(df_metas):
    faltantes = [c for c in COLUMNAS_METAS_REQUERIDAS if c not in df_metas.columns]
    if faltantes:
        return False, f"El archivo de metas no contiene: {', '.join(faltantes)}"

    df_metas["CITE"] = df_metas["CITE"].astype(str).str.strip()
    if df_metas["CITE"].duplicated().any():
        duplicados = df_metas.loc[df_metas["CITE"].duplicated(keep=False), "CITE"].unique()
        return False, "Hay CITE duplicados en metas: " + ", ".join(map(str, duplicados))

    for col in COLUMNAS_METAS_REQUERIDAS[1:]:
        if pd.to_numeric(df_metas[col], errors="coerce").isna().any():
            return False, f"La columna '{col}' contiene metas vacías o no numéricas."

    return True, "Archivo de metas válido."


def validar_listado_up(df_up):
    faltantes = [c for c in COLUMNAS_UP_REQUERIDAS if c not in df_up.columns]
    if faltantes:
        return False, f"El listado de UP no contiene: {', '.join(faltantes)}", []

    df_up["CITE"] = df_up["CITE"].astype(str).str.strip()
    advertencias = []

    if (df_up["CITE"] == "").any():
        return False, "Existen registros del listado UP sin CITE.", []

    if df_up["RUC/DNI/CE/OTROS"].isna().any():
        advertencias.append("Existen registros del listado UP sin RUC/DNI/CE/OTROS.")

    if df_up["RAZON SOCIAL / APELLIDOS Y NOMBRES"].isna().any():
        advertencias.append("Existen registros del listado UP sin razón social/nombre.")

    return True, "Listado UP válido.", advertencias


def validar_cruces(df_consolidado, df_metas, df_up):
    """Comprueba coincidencia exacta de nombres entre las tres fuentes."""
    cites = set(df_consolidado["cite_ut"].dropna().astype(str).str.strip())
    metas = set(df_metas["CITE"].dropna().astype(str).str.strip())
    listado = set(df_up["CITE"].dropna().astype(str).str.strip())

    sin_meta = sorted(cites - metas)
    sin_listado = sorted(cites - listado)
    mensajes = []
    if sin_meta:
        mensajes.append("Sin meta: " + ", ".join(sin_meta))
    if sin_listado:
        mensajes.append("Sin listado UP Indicador 1: " + ", ".join(sin_listado))

    return len(mensajes) == 0, mensajes
