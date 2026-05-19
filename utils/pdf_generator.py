from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Table
from reportlab.platypus import TableStyle

def generate_pdf(dataframe, filename="User_Report.pdf"):
    doc = SimpleDocTemplate(filename)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("Insider Threat Detection Report", styles["Title"]))
    elements.append(Spacer(1, 0.5 * inch))

    table_data = [list(dataframe.columns)] + dataframe.values.tolist()
    table = Table(table_data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return filename
