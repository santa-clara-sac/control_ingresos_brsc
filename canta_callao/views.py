from django.shortcuts import render
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# ====== CONFIGURACIÓN DE GOOGLE SHEETS ======
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# KEY = 'key_cromosoma.json'
KEY = 'key_brsc.json'
SPREADSHEET_ID = '1x_bmJ3JRUaaTE57UgmOFgdGpwqbQzg__sLEsYBX1C-g'
creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

def canta_callao(request):
    # Leer columnas A–E
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='1!A:E'
    ).execute()

    values = result.get('values', [])

    # Manejo básico
    if not values:
        return render(request, "home.html", {"headers": [], "rows": []})

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
    }

    return render(request, 'canta_callao/colegio_jennifer.html', context)

