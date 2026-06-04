import camelot
import pandas as pd

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
    