import argparse
import requests
from datetime import datetime

API_BASE_URL="http://localhost:3333"

parser = argparse.ArgumentParser(description="Given a storage it exports the inventory as rows of PN, Desc and Qty.")
parser.add_argument("--storage", type=str, help="Storage name given by \"fullName\". Case insensitive.")
parser.add_argument("--list", action="store_true", help="Retrieve all storage's \"fullName\" as lowercase.")
parser.add_argument("--title", type=str, help="Title of the document.")
parser.add_argument("--pdf", action="store_true", help="Write result to the standard output as PDF.")
parser.add_argument("--csv", action="store_true", help="Write result to the standard output as CSV.")
parser.add_argument("--tsv", action="store_true", help="Write result to the standard output as TSV.")

args = parser.parse_args()

if not args.storage and not args.list:
    print("Must execute using --storage <storage>, --list or --help")
    exit(1)

session = requests.Session()
r = session.get("http://localhost:3333/storage")

if args.list:
    for entry in r.json():
        print(entry["storage"]["fullName"].lower())
    exit(0)

storage_id = None
storage_fullName = args.storage.lower()
for entry in r.json():
    entry_fullName = entry["storage"]["fullName"].lower()
    if storage_fullName == entry_fullName:
        storage_id = entry["id"]

if not storage_id:
    print("Not found.")
    exit(2)

r = session.get(f"http://localhost:3333/storage/{storage_id}/inventory?nested=false")
part_list1 = []
for entry in r.json():
    qty = entry["inventory"]["qty"]
    part_id = entry["inventory"]["part"]
    part_list1.append(tuple((part_id, qty)))

part_list2 = [tuple(("qty", "mpn", "manufacturer", "description"))]
for part_id,qty in part_list1:
    entry = session.get(f"http://localhost:3333/parts/{part_id}").json()
    mpn = entry["part"]["mpn"]
    manufacturer = entry["part"]["manufacturer"]
    description = entry["part"]["description"]
    part_list2.append(tuple((qty, mpn, manufacturer, description)))

headers = part_list2[0]
rows = part_list2[1:]

if args.csv:
    exit(0)

if args.tsv:
    exit(0)

if args.pdf:
    from fpdf import FPDF
    import re
    # Crear PDF
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False, margin=15)
    pdf.add_page()
    FONT = "dejavu-sans"
    pdf.add_font(FONT, style="", fname="DejaVuSans.ttf")
    pdf.add_font(FONT, style="b", fname="DejaVuSans.ttf")
    pdf.set_font(FONT, size=10)

    def get_text_height(text, font_size, col_width):
        # Usamos multi_cell para calcular cuántas líneas ocupa el texto
        pdf.set_font(FONT, size=font_size)
        return 2 + pdf.get_string_width(text) * font_size / col_width   # Aproximación de la altura
    
    def calculate_lines(text, col_width, font_size=12):
        if 0 == len(text):
            return 1
        # Obtener el ancho del texto en la fuente actual
        pdf.set_font(FONT, size=font_size)
        text_width = pdf.get_string_width(text)
        
        # Calcular cuántos caracteres caben en una línea
        chars_per_line = col_width / (text_width / len(text))
        
        # Calcular cuántas líneas ocuparía el texto
        lines_needed = (len(text) // chars_per_line) + (1 if len(text) % chars_per_line > 0 else 0)
        return lines_needed
    
    # Agregar encabezados
    pdf.set_font(FONT, style="B", size=12)
    col_widths = [25, 70, 70, 100]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, str(header), border=1, align="C")
    pdf.ln()

    x_pos_ini = pdf.get_x()
    y_pos_ini = pdf.get_y()
    y_pos = pdf.get_y()
    for row in rows:
        max_height = 0
        cell_heights = []
        for i, cell in enumerate(row):
            cell_text = str(cell)
            text_height = get_text_height(cell_text, font_size=10, col_width=col_widths[i])
            cell_heights.append(text_height)
            max_height = max(max_height, text_height)

        x_pos = x_pos_ini
        for i, cell in enumerate(row):
            pdf.set_xy(x_pos, y_pos)
            s = re.sub(r"[\n\t\x81\x8e]*", "", str(cell))
            s = re.sub(r"\s+", " ", s)
            lines_occupied = calculate_lines(s, col_widths[i])
            pdf.multi_cell(col_widths[i], max_height/lines_occupied, s, border=1, align="L")
            x_pos += col_widths[i]
        y_pos += max_height
        if y_pos > 180:
            pdf.add_page()
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, str(header), border=1, align="C")
            pdf.ln()
            y_pos = pdf.get_y()

    pdf.output(f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {storage_fullName}.pdf")
    exit(0)

# Determina el ancho de las columnas
col_widths = [max(len(str(row[i])) for row in part_list2) for i in range(len(headers))]

# Formato de encabezados
header_row = " | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
print(header_row)
print("-" * len(header_row))

# Formato de filas
for row in rows:
    print(" | ".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(row))))
exit(0)
