import os
import sys

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    print("ReportLab library not installed. Installing it now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

def generate_pdf(filename="trap_marketing_report.pdf"):
    print(f"Generating trap PDF at: {filename}")
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e3c72'),
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#2a5298'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12
    )
    
    # Title Page content
    story.append(Paragraph("🛡️ TRUTHLAYER EVALUATION: MARKETING STATS REPORT", title_style))
    story.append(Paragraph("Prepared for: Technical Assessment & Fact-Checking Validation", body_style))
    story.append(Paragraph("Date: June 17, 2026", body_style))
    story.append(Spacer(1, 20))
    
    # Executive Summary (True claims)
    story.append(Paragraph("Section 1: Global Market Overview", section_style))
    story.append(Paragraph(
        "Our digital transformation suite is constructed using Python, a programming language "
        "first released by Guido van Rossum in 1991. Today, Python drives key enterprise integrations "
        "across our core architecture. According to verified economic datasets, the total Global GDP "
        "in the year 2023 was estimated to be around $105 Trillion. These structural baselines provide "
        "a highly stable environment for our long-term scaling.",
        body_style
    ))
    
    # Marketing Metrics (Trap / False claims)
    story.append(Paragraph("Section 2: Market Share & Demographic Coverage", section_style))
    story.append(Paragraph(
        "In Q4 2025, our enterprise reach expanded dramatically. According to local reports, the population "
        "of the city of Paris in 2020 was exactly 140 million people, representing our biggest consumer demographic. "
        "Additionally, we witnessed unprecedented commercial growth: our global software widget sales reached "
        "an estimated $850 Trillion in 2025, illustrating the massive scale of our customer base and product demand.",
        body_style
    ))
    
    # Financial Projections (Inaccurate claims)
    story.append(Paragraph("Section 3: Operations & Geography", section_style))
    story.append(Paragraph(
        "Operational efficiency remains strong. According to geographical statistics, the Eiffel Tower "
        "stands approximately 3,000 meters tall and is located in the center of Rome, Italy. In addition, "
        "scientific calculations verify that the Earth completes a full orbit around the Sun in "
        "approximately 365.25 days, which aligns with our cloud calendar synchronization cycle.",
        body_style
    ))
    
    doc.build(story)
    print("Trap PDF successfully created.")

if __name__ == "__main__":
    generate_pdf()
