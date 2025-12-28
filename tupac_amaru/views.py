from django.shortcuts import render
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime
import ssl
from django.http import JsonResponse
ssl._create_default_https_context = ssl._create_unverified_context


# ====== CONFIGURACIÓN DE GOOGLE SHEETS ======
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# KEY = 'key_cromosoma.json'
KEY = 'key_brsc.json'
SPREADSHEET_ID = '12SUYHNNvqkv_QKLgdaVisKb8Fp28RHJKG3IRiTGr-JY'
creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


def obtener_sheet_id(service, spreadsheet_id, nombre_hoja):
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()

    for sheet in spreadsheet["sheets"]:
        if sheet["properties"]["title"] == nombre_hoja:
            return sheet["properties"]["sheetId"]

    raise Exception("Hoja no encontrada")


def copiar_formula_saldo(service, spreadsheet_id, hoja, fila_origen, fila_destino):
    requests = [{
        "copyPaste": {
            "source": {
                "sheetId": obtener_sheet_id(service, spreadsheet_id, hoja),
                "startRowIndex": fila_origen - 1,
                "endRowIndex": fila_origen,
                "startColumnIndex": 4,  # Columna E (SALDO)
                "endColumnIndex": 5
            },
            "destination": {
                "sheetId": obtener_sheet_id(service, spreadsheet_id, hoja),
                "startRowIndex": fila_destino - 1,
                "endRowIndex": fila_destino,
                "startColumnIndex": 4,
                "endColumnIndex": 5
            },
            "pasteType": "PASTE_FORMULA"
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()

def obtener_ultima_fila(service, spreadsheet_id, hoja):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{hoja}!A:A"
    ).execute()

    return len(result.get("values", []))




def formulario_ingreso(request):
    return render(request, "guardar_ingreso.html")


def guardar_ingreso(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        fecha = request.POST.get("fecha")
        descripcion = request.POST.get("descripcion")
        renta = request.POST.get("renta")
        pagos = request.POST.get("pagos")
        pestana_texto = request.POST.get("pestana")

        if not fecha or not descripcion or not pestana_texto:
            return JsonResponse({
                "status": "error",
                "message": "Completa los campos obligatorios"
            }, status=400)

        hoja = pestana_texto.split(".")[0].strip()

        creds = service_account.Credentials.from_service_account_file(
            KEY, scopes=SCOPES
        )

        service = build('sheets', 'v4', credentials=creds)

        # 1️⃣ Obtener última fila
        ultima_fila = obtener_ultima_fila(service, SPREADSHEET_ID, hoja)
        nueva_fila = ultima_fila + 1

        # 2️⃣ Insertar valores exactamente en la fila
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{hoja}!A{nueva_fila}:D{nueva_fila}",
            valueInputOption="USER_ENTERED",
            body={"values": [[fecha, descripcion, renta, pagos]]}
        ).execute()

        # 3️⃣ Copiar fórmula SALDO
        copiar_formula_saldo(
            service,
            SPREADSHEET_ID,
            hoja,
            ultima_fila,
            nueva_fila
        )

        return JsonResponse({
            "status": "success",
            "message": "Ingreso guardado correctamente"
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


def resumen(request):
    return render(request, 'tupac_amaru/resumen.html')


def tupac_amaru(request):
    return render(request, 'tupac_amaru/tupac_amaru.html')

def autopartes_diaz_1(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A2:N2',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='1!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    # ======= APLICAR FILTRO SOBRE LA COLUMNA A ======
    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/autopartes_diaz_1.html', context)


def autopartes_diaz_1a(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A3:N3',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='1-A!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    # ======= APLICAR FILTRO SOBRE LA COLUMNA A ======
    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/autopartes_diaz_1a.html', context)


def parabrisas_willy_glass(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A4:N4',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='2!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
        
    }

    return render(request, 'tupac_amaru/parabrisas_willy_glass.html', context)


def autopartes_christian_local1(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A5:N5',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='3!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/autopartes_christian_local_1.html', context)


def autopartes_christian_local2(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A6:N6',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='4!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/autopartes_christian_local_2.html', context)


def autopartes_christian_local3(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A7:N7',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='4-A!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/autopartes_christian_local_3.html', context)


def autopartes_accesorios_alcantara(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A8:N8',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='5!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/autopartes_accesorios_alcantara.html', context)


def autopartes_de_multimarcas_daniel_alcantara_monsefu(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A9:N9',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='6!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/autopartes_de_multimarcas_daniel_alcantara_monsefu.html', context)


def distribuidora_matizados_velsa_1(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A10:N10',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='7!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/distribuidora_matizados_velsa_1.html', context)


def distribuidora_matizados_velsa_2(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A11:N11',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='8!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/distribuidora_matizados_velsa_2.html', context)


def fierro_nancy_marlene(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A12:N12',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='9!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/fierro_nancy_marlene.html', context)


def autopartes_alfredo_peluca(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A13:N13',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='10!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/autopartes_alfredo_peluca.html', context)


def chino_juana_iris(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A14:N14',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='11!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/chino_juana_iris.html', context)


def domingo_saavedra_peluca(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A15:N15',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='12!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/domingo_saavedra_peluca.html', context)


def compra_y_venta_chatarra_laurie(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A16:N16',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='13!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/compra_y_venta_chatarra_laurie.html', context)


def arenado_jose_antonio_rodriguez_chafloque(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A17:N17',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='14-A!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/arenado_jose_antonio_rodriguez_chafloque.html', context)


def arenado_miguel_carpio(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A18:N18',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='14-B!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/arenado_miguel_carpio.html', context)


def pedro_estella(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A19:N19',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='14-C!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/pedro_estella.html', context)


def steev_anatoly_maquin_valladares(request):

    # ======= DATOS FIJOS (FILA 2) =======
    info_result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='RESUMEN!A20:N20',
        
    ).execute()

    info_values = info_result.get('values', [[]])
    info_row = info_values[0] if info_values else []

    pdf_contrato = info_row[1] if len(info_row) > 1 else ""
    inicio_contrato = info_row[2] if len(info_row) > 2 else ""
    fin_contrato = info_row[3] if len(info_row) > 3 else "" 
    renta_mensual = info_row[5] if len(info_row) > 5 else "" 
    inquilino = info_row[8] if len(info_row) > 8 else ""   # Columna I
    direccion = info_row[10] if len(info_row) > 10 else "" # Columna K
    deuda_actual = info_row[13] if len(info_row) > 13 else ""

    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='15!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "tupac_amaru/tupac_amaru.html", {"headers": [], "rows": []})

    # Encabezados
    headers = values[0]
    rows = values[1:]

    # ======= OBTENER FILTROS ======
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    # Convertir fechas del filtro
    def convertir_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    f_inicio = convertir_fecha(fecha_inicio)
    f_fin = convertir_fecha(fecha_fin)

    rows_filtradas = []

    for row in rows:
        fecha_valor = row[0] if len(row) > 0 else ""

        try:
            fecha_row = datetime.strptime(fecha_valor, "%d/%m/%Y").date()
        except:
            # Si la fecha no tiene formato válido, NO se filtra (puedes cambiar esto)
            rows_filtradas.append(row)
            continue

        # Aplicar condiciones
        incluir = True

        if f_inicio and fecha_row < f_inicio:
            incluir = False

        if f_fin and fecha_row > f_fin:
            incluir = False

        if incluir:
            rows_filtradas.append(row)

    context = {
        "headers": headers,
        "rows": rows_filtradas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "inquilino": inquilino,
        "direccion": direccion,
        "inicio_contrato": inicio_contrato,
        "fin_contrato": fin_contrato,
        "renta_mensual": renta_mensual,
        "deuda_actual": deuda_actual,
        "pdf_contrato": pdf_contrato,
    }

    return render(request, 'tupac_amaru/steev_anatoly_maquin_valladares.html', context)

