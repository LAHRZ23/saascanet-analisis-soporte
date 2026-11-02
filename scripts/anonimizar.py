"""Anonimiza el CSV exportado de SAASCANET y agrega categorías.
Uso: python anonimizar.py <csv_original> <csv_salida>
Elimina nombres, comentarios y notas (texto libre con datos personales y credenciales)."""
import sys, re, unicodedata, pandas as pd
src, out = sys.argv[1], sys.argv[2]
df = pd.read_csv(src)

def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', s).strip()

# --- Tema del ticket, inferido del texto libre (que después se elimina) ---
REGLAS = [
    ('Internet y red',            r'internet|\bred\b|conexi|access point|switch|wifi'),
    ('Grabación y copia de CD',   r'\bcd\b|cd-r'),
    ('Puertos USB',               r'usb'),
    ('Impresión y escaneo',       r'imprim|impresora|impresi|escaner|escaneo'),
    ('Fuentes tipográficas',      r'fuente|gotham|gothan'),
    ('Accesos, correo y sistemas',r'correo|teams|contrasen|autentic|acceso|sgi|sistema de gestio|sistema|intranet|reunion|nombres en mi'),
    ('Publicaciones y contenido web', r'hipervinculo|comunicado|publicaci|ipomex|nube|carpeta'),
    ('Software y licencias',      r'licencia|adobe|acrobat|office|ofimatic|chrome|nitro|framework|frame word|winrar|pdf|one drive|actualiza|software|excel'),
    ('Rendimiento y hardware',    r'formateo|recupera|lent|trab|mantenimiento|mouse|laptop|borro'),
]
def tema(row):
    # Primero se clasifica con lo que escribió el usuario; si no basta, con la nota del técnico
    for campo in ('Comentarios', 'Nota'):
        txt = norm(row[campo]) if pd.notna(row[campo]) else ''
        for nombre, patron in REGLAS:
            if re.search(patron, txt):
                return nombre
    return 'Otro'

# --- Tipo de equipo, normalizado desde un campo de texto libre ---
def equipo(e):
    e = norm(e)
    if re.search(r'lap|acer|hp laptop', e): return 'Laptop'
    if re.search(r'escritorio|pc|saasca|2016', e): return 'PC de escritorio'
    if re.search(r'impresora|mouse|lector', e): return 'Periférico'
    return 'Sin especificar'

df['tema'] = df.apply(tema, axis=1)
df['equipo_tipo'] = df['Equipo'].apply(equipo)

# --- Seudónimos: mismos nombres (aunque cambien mayúsculas o acentos) -> mismo código ---
usuarios = {n: f'Usuario {i:02d}' for i, n in enumerate(sorted(df['Nombre'].map(norm).unique()), 1)}
tecnicos = {n: f'Técnico {chr(65+i)}' for i, n in enumerate(sorted(df['Atendió'].map(norm).unique()))}

anon = pd.DataFrame({
    'folio': df['Folio'],
    'usuario': df['Nombre'].map(norm).map(usuarios),
    'area': df['Área'],
    'equipo_tipo': df['equipo_tipo'],
    'tipo_formulario': df['Tipo'],
    'tema': df['tema'],
    'estatus': df['Estatus'],
    'registrado': df['Registrado'],
    'resuelto': df['Resuelto'],
    'tecnico': df['Atendió'].map(norm).map(tecnicos),
    'n_participantes': df['Participantes'].fillna('').str.split(',').str.len(),
})
anon.to_csv(out, index=False, encoding='utf-8')
print(anon['tema'].value_counts(), '\n', anon['equipo_tipo'].value_counts())
