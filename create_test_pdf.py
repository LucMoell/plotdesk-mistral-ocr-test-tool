#!/usr/bin/env python3
"""
Simple script to create a test PDF file for OCR testing
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

def create_test_pdf():
    """Create a simple test PDF with text content"""
    
    # Create test_files directory if it doesn't exist
    os.makedirs('test_files', exist_ok=True)
    
    # Create PDF
    filename = "test_files/test_document.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    story.append(Paragraph("Test Document für Mistral OCR", styles['Title']))
    story.append(Spacer(1, 20))
    
    # Add content
    content = [
        "Dies ist ein Test-Dokument für die Mistral OCR Test Suite.",
        "Das Dokument enthält verschiedene Arten von Text, um die OCR-Fähigkeiten zu testen.",
        "",
        "Seite 1 enthält:",
        "- Deutschen Text mit Umlauten (ä, ö, ü)",
        "- Verschiedene Schriftgrößen und -stile",
        "- Zahlen und Sonderzeichen: 1234567890 !@#$%^&*()",
        "- Mehrzeilige Absätze mit unterschiedlichem Inhalt",
        "",
        "Dieser Text dient dazu, die Token-Verbrauch und Performance der OCR-Modelle zu testen.",
        "Besonders wichtig ist die Analyse von Token-Limits bei verschiedenen Dokumentgrößen.",
        "",
        "Weitere Test-Inhalte:",
        "• Aufzählungspunkte",
        "• Verschiedene Formatierungen",
        "• Lange Sätze mit vielen Wörtern",
        "• Technische Begriffe und Abkürzungen",
        "",
        "Das Ziel ist es, zu verstehen, wie die verschiedenen OCR-Provider mit unterschiedlichen",
        "Dokumenttypen umgehen und wo Token-Limits auftreten können."
    ]
    
    for line in content:
        if line.startswith('-') or line.startswith('•'):
            story.append(Paragraph(line, styles['Normal']))
        elif line.strip() == "":
            story.append(Spacer(1, 12))
        else:
            story.append(Paragraph(line, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    print(f"✓ Test PDF created: {filename}")
    print(f"📄 File size: {os.path.getsize(filename) / 1024:.1f} KB")
    
    return filename

if __name__ == "__main__":
    create_test_pdf()
