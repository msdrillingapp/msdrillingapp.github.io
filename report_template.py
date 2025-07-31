from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Table, Spacer, Paragraph, Image
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.platypus.doctemplate import SimpleDocTemplate
from io import BytesIO

class PileReportHeader:
    def __init__(self, *, logo_path=None, filename, project, location, pile_props,  meta_info, notes=None):
        self.logo_path = logo_path
        self.project = project
        self.location = location
        self.pile_props = pile_props
        self.meta_info = meta_info
        self.notes = notes or []
        self.filename =filename

    def draw_header(self,canvas: Canvas, doc):
        width, height = landscape(LETTER)
        canvas.saveState()
        # === 1. Draw Company Logo ===
        logo_width = 1.25 * inch
        logo_height = 1.0 * inch
        logo_x = 0.5 * inch
        logo_y = height - logo_height - 0.25 * inch
        if self.logo_path:
            try:
                canvas.drawImage(self.logo_path, logo_x, logo_y, width=logo_width, height=logo_height, mask='auto')
            except:
                canvas.setFont("Helvetica", 6)
                canvas.drawString(logo_x, logo_y + 0.4 * inch, "[Logo Not Found]")


        # Project & Location Info
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(0.55 * inch, height - 1.5 * inch, "Project:")
        canvas.setFont("Helvetica", 7)
        canvas.drawString(1 * inch, height - 1.5 * inch, self.project)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(0.55 * inch, height - 1.75 * inch, "Location:")
        canvas.setFont("Helvetica", 7)
        canvas.drawString(1.1 * inch, height - 1.75 * inch, self.location)


        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(2 * inch, height - 0.5 * inch, "Morris-Shea Bridge Co., Inc.")
        canvas.setFont("Helvetica", 7)
        canvas.drawString(2 * inch, height - 0.75 * inch, "609 South 20th Street")
        canvas.drawString(2 * inch, height - 1.0 * inch, "Birmingham, AL 35210")

        # Right-aligned CPT Info
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(width - 0.5 * inch, height - 1.0 * inch, self.meta_info.get("CPT ID", "CPT-XX"))

        canvas.setFont("Helvetica", 7)
        meta_lines = [
            f"Total depth: {self.meta_info.get('depth', '?')} ft, Date: {self.meta_info.get('date', '?')}",
            f"Surface Elevation: {self.meta_info.get('elevation', '?')} ft, GWL: {self.meta_info.get('gwl', '?')} ft",
            f"Coords: lat {self.meta_info.get('lat', '?')}° lon {self.meta_info.get('lon', '?')}°",
            f"Cone Type: {self.meta_info.get('cone_type', '?')}",
            f"Cone Operator: {self.meta_info.get('operator', '?')}",
        ]
        for i, line in enumerate(meta_lines):
            canvas.drawRightString(width - 0.5 * inch, height - (1.15 + i * 0.15) * inch, line)

            # --- Horizontal line before Pile Properties ---
        line_y = height - 1.8 * inch
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.5)
        canvas.line(0.5 * inch, line_y, width - 0.5 * inch, line_y)


        # Pile Properties
        # === Pile Properties ===
        canvas.setFont("Helvetica-Bold", 7)
        x = 0.5 * inch
        y_start = height - 2.3 * inch
        for i, (key, value) in enumerate(self.pile_props.items()):
            # if i == 0:
            #     canvas.setFillColor(colors.black)
            #     canvas.drawString(x, y_start, "Pile properties")
            #     canvas.setFillColor(colors.black)
            #     # y_offset = 0.15 * inch
            # else:
                canvas.setFont("Helvetica", 7)
                canvas.drawString(x, y_start + i * 0.15 * inch, f"{key}: {value}")


        canvas.restoreState()


    def build_pdf(self,images=None):


        if isinstance(self.filename, BytesIO):
            doc = SimpleDocTemplate(self.filename, pagesize=landscape(LETTER),
                                    rightMargin=0.5 * inch, leftMargin=0.5 * inch,
                                    topMargin=2.25 * inch, bottomMargin=0.5 * inch)
        else:
            doc = BaseDocTemplate(self.filename, pagesize=landscape(LETTER),
                                  rightMargin=0.5 * inch, leftMargin=0.5 * inch,
                                  topMargin=2.25 * inch, bottomMargin=0.5 * inch)

        frame = Frame(doc.leftMargin, doc.bottomMargin,
                      doc.width, doc.height, id='normal')

        doc.addPageTemplates([PageTemplate(id='report', frames=frame, onPage=self.draw_header)])

        # Assemble into table (1 row, 3 columns)
        # table = Table([images], colWidths=[3 * inch] * 3)
        from reportlab.platypus import Image as RLImage
        from PIL import Image as PILImage
        # Build story
        story = []

        # === Image scaling ===
        img_io = images[0]
        img_io.seek(0)

        with PILImage.open(img_io) as pil_img:
            img_width, img_height = pil_img.size
            available_width = doc.width
            available_height = doc.height - 0.3 * inch  # Safety padding

            # Maintain aspect ratio
            aspect = img_height / img_width
            scaled_width = available_width
            scaled_height = scaled_width * aspect

            if scaled_height > available_height:
                scaled_height = available_height
                scaled_width = scaled_height / aspect

            print(f"Scaled image size: {scaled_width} x {scaled_height}")

        img_io.seek(0)
        image = RLImage(img_io, width=scaled_width, height=scaled_height)
        story.append(image)

        # Add optional spacing
        # story.append(Spacer(1, 0.2 * inch))
        # wrapped_images = [RLImage(img, width=8 * inch, height=10 * inch) for img in images]
        # table = Table([wrapped_images], colWidths=[8 * inch] * len(wrapped_images))
        #
        # story = []
        # story.append(Spacer(1, 0.2 * inch))
        # story.append(table)

        doc.build(story, onFirstPage=self.draw_header)

if __name__ == "__main__":
    logo_path = "C:\\Inventzia_Dennis\\msdrillingapp.github.io\\assets\\MSB.logo.JPG"  # Replace with your logo file name
    header = PileReportHeader(
        logo_path=logo_path,
        filename="C:\\Temp\\pile_report.pdf",
        project="1640 - Margaritaville",
        location="Orange Beach, AL",
        pile_props={
            "Pile diameter": "1.17 ft",
            "Pile Model": "1.17 ft",
        },
        meta_info={
            "CPT ID": "CPT-01",
            "depth": "66.93",
            "date": "5/17/2025",
            "elevation": "100.0",
            "gwl": "6.00",
            "lat": "30.29592",
            "lon": "-87.62992",
            "cone_type": "1-CPT009-15",
            "operator": "CEK"
        },
        notes=[
            "Replace with Pile Diameter",
            'and Pile Model as "LCPC" bored piles'
        ]
    )

    header.build_pdf()
