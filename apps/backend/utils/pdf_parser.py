import camelot
import pandas as pd
import fitz  # PyMuPDF
import pymupdf4llm
import re


def extraer_con_pymupdf_tables(pdf_bytes: bytes) -> pd.DataFrame:
    """
    Usa PyMuPDF find_tables() con motor geométrico para extraer tablas.
    No convierte a Markdown. Preserva la estructura tabular original basada en
    coordenadas y líneas de tabla. Valida encabezados mínimos y descarta basura.

    Soporta dos escenarios:
    - Tablas con bordes vectoriales (detecta filas individuales).
    - Tablas sin bordes donde find_tables() colapsa todo en una celda
      (parsea el contenido textual de la celda, cada producto por línea).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # ── Palabras clave ──────────────────────────────────────────────
    keywords_codigo = {"codigo", "referencia", "item", "#codigo", "código"}
    keywords_cantidad = {"cantidad", "unidad", "despachada", "cant"}
    keywords_costo = {"costo", "precio", "valor unitario", "precio unid", "vr. unitario", "valor"}

    def tiene_encabezados_minimos(row):
        row_text = " ".join(str(c).strip().lower().replace("\n", " ") for c in row if c)
        has_codigo = any(k in row_text for k in keywords_codigo)
        has_cantidad = any(k in row_text for k in keywords_cantidad)
        has_costo = any(k in row_text for k in keywords_costo)
        has_descrip = "descrip" in row_text
        return has_codigo and has_cantidad and has_costo and has_descrip

    def es_fila_valida(row):
        if not row or not row[0]:
            return False
        val = str(row[0]).strip()
        if not val:
            return False
        # El primer token (código producto) debe ser numérico
        primer_token = val.split()[0] if val.split() else ''
        if not primer_token.isdigit():
            return False
        val_lower = val.lower()
        if any(word in val_lower for word in ("total", "subtotal", "iva", "página", "pagina", "numero", "nota")):
            return False
        return True

    # ── Helper: parsea líneas de producto desde el texto de una celda ──
    def parsear_celda_unificada(cell_text):
        """
        El texto contiene todos los productos en líneas separadas por \\n.
        Cada línea de producto tiene formato:
          CODIGO DESCRIPCION ... carton 0 cantidad precio unitario vr_bruto ... neto_total
        Los últimos 12 tokens son siempre campos numéricos.
        tokens[-10] = cantidad, tokens[-9] = precio unitario.
        """
        lineas = cell_text.split('\n')
        header_encontrado = False
        productos = []

        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            if 'total items' in linea.lower():
                continue
            if re.match(r'^[_\-=\s]+$', linea):
                continue

            # Detectar línea de encabezado
            if not header_encontrado:
                linea_lower = linea.lower()
                if any(k in linea_lower for k in keywords_codigo):
                    header_encontrado = True
                continue

            # Parsear línea de producto
            tokens = linea.split()
            if len(tokens) < 13:
                continue
            codigo = tokens[0]
            if not codigo.isdigit():
                continue
            descripcion = ' '.join(tokens[1:-12])
            cantidad_str = tokens[-10]
            precio_str = tokens[-9]
            productos.append([codigo, descripcion, cantidad_str, precio_str])

        return productos if productos else None

    # ── Búsqueda en páginas ─────────────────────────────────────────
    header_row = None
    all_data_rows = []
    header_cells_contenido = []  # guarda celdas con posible data inline

    for page_num in range(len(doc)):
        page = doc[page_num]
        for strategy in ("lines", "text"):
            tf = page.find_tables(strategy=strategy)
            if not tf.tables:
                continue
            for table in tf.tables:
                data = table.extract()
                if not data:
                    continue

                # ── Escenario A: filas individuales ──
                for i, row in enumerate(data):
                    if tiene_encabezados_minimos(row):
                        header_row = row
                        for data_row in data[i + 1:]:
                            if es_fila_valida(data_row):
                                all_data_rows.append(data_row)
                        # Guardar celdas de la fila header por si tienen data inline
                        header_cells_contenido = [str(c) for c in row if c and '\n' in str(c)]
                        break

                if header_row and len(all_data_rows) >= 2:
                    break

                # ── Escenario B: celda unificada ──
                # Si el header tiene celdas multilínea, buscar data inline
                if header_cells_contenido:
                    for cell_text in header_cells_contenido:
                        productos = parsear_celda_unificada(cell_text)
                        if productos:
                            header_row = ["Codigo", "Descripcion", "Cantidad", "Costo"]
                            all_data_rows = productos
                            break

                if header_row:
                    break

                # ── Escenario C: buscar en cualquier celda (sin header previo) ──
                for row in data:
                    for cell in row:
                        if not cell or '\n' not in str(cell):
                            continue
                        productos = parsear_celda_unificada(str(cell))
                        if productos:
                            header_row = ["Codigo", "Descripcion", "Cantidad", "Costo"]
                            all_data_rows = productos
                            break
                    if header_row:
                        break

            if header_row:
                break
        if header_row:
            break

    doc.close()

    if not header_row:
        raise ValueError(
            "Tabla no detectada: no se encontraron encabezados válidos "
            "(codigo/referencia, cantidad, costo) en el PDF."
        )
    if not all_data_rows:
        raise ValueError(
            "Tabla no detectada: no se encontraron filas de datos válidas "
            "después de los encabezados."
        )

    df = pd.DataFrame([header_row] + all_data_rows)
    return df


def extraer_con_camelot(pdf_bytes: bytes) -> pd.DataFrame:
    """
    Usa Camelot con flavor='stream' para detectar tablas basadas en espacios.
    """
    # Guardamos el archivo temporalmente porque Camelot necesita una ruta de archivo
    with open("temp_invoice.pdf", "wb") as f:
        f.write(pdf_bytes)
        
    try:
        # stream detecta las columnas basándose en el espacio en blanco (el algoritmo perfecto para Colombina)
        tables = camelot.read_pdf("temp_invoice.pdf", flavor='stream', pages='all', edge_tol=50)
        
        if len(tables) == 0:
            raise ValueError("Camelot no encontró tablas en el PDF.")
        
        # Concatenamos todas las tablas encontradas en una sola
        df_list = [table.df for table in tables]
        full_df = pd.concat(df_list, ignore_index=True)
        
        return full_df
        
    except Exception as e:
        raise ValueError(f"Error procesando con Camelot: {str(e)}")
    

def extraer_con_markdown(pdf_bytes: bytes) -> pd.DataFrame:
    """
    Convierte un PDF a Markdown usando PyMuPDF localmente y 
    lo transforma en un DataFrame compatible con la lógica del sistema.
    """
    # 1. Cargar el documento desde la memoria (bytes)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # 2. Convertir el documento entero a Markdown
    md_text = pymupdf4llm.to_markdown(doc)
    
    # 3. Extraer las filas que pertenecen a tablas
    lineas = md_text.split('\n')
    filas = []
    
    for linea in lineas:
        # Filtramos: debe contener el separador de tabla '|' 
        # y NO ser una línea separadora de Markdown (ej. |---|---|)
        if '|' in linea and not re.match(r'^\|[\-\|\s]+\|$', linea.strip()):
            
            # Limpiar asteriscos de negrita (**) y espacios extra
            linea_limpia = linea.replace('**', '').strip()
            
            # Separar las columnas
            columnas = [col.strip() for col in linea_limpia.split('|')]
            
            # Al hacer split con '|' al inicio y final, quedan strings vacíos en los extremos. Los quitamos.
            if columnas and columnas[0] == '': 
                columnas.pop(0)
            if columnas and columnas[-1] == '': 
                columnas.pop()
            
            if columnas:
                filas.append(columnas)
                
    if not filas:
        raise ValueError("No se detectaron tablas estructuradas en el documento.")
        
    # 4. Convertimos a DataFrame para mantener la compatibilidad con process_receipt_logic
    df = pd.DataFrame(filas)
    return df
    