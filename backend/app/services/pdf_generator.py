import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_audit_pdf(report_data: dict, output_path: str):
    """
    Generate a professional PDF report for the website audit using reportlab.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=20,
        alignment=1 # Center
    )
    
    heading2_style = ParagraphStyle(
        name="Heading2Style",
        parent=styles["Heading2"],
        fontSize=18,
        textColor=colors.HexColor("#34495E"),
        spaceBefore=15,
        spaceAfter=10,
    )

    normal_style = styles["Normal"]
    
    elements = []
    
    # 1. Cover Page
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("Website Auditor", title_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>Comprehensive Audit Report</b>", title_style))
    elements.append(Spacer(1, 40))
    
    elements.append(Paragraph(f"<b>Website:</b> {report_data.get('website_url', 'N/A')}", styles["Heading3"]))
    elements.append(Paragraph(f"<b>Audit Date:</b> {report_data.get('created_at', 'N/A')}", styles["Heading3"]))
    elements.append(Paragraph(f"<b>Audit Score:</b> {report_data.get('audit_score', 'N/A')}/100", styles["Heading3"]))
    
    elements.append(PageBreak())
    
    # 2. Executive Summary
    elements.append(Paragraph("Executive Summary", heading2_style))
    summary_text = f"This report provides a comprehensive analysis of {report_data.get('website_url', 'the website')}. " \
                   f"The overall audit score is {report_data.get('audit_score', 'N/A')} out of 100. " \
                   f"A total of {report_data.get('issues_found', 0)} issues were identified that require attention."
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 20))
    
    # 3. Category Breakdown
    elements.append(Paragraph("Category Breakdown", heading2_style))
    category_scores = report_data.get("category_scores", {})
    if category_scores:
        cat_data = [["Category", "Score"]]
        for cat, score in category_scores.items():
            cat_data.append([cat.capitalize(), str(score)])
        
        cat_table = Table(cat_data, colWidths=[200, 100])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#ECF0F1")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(cat_table)
    else:
        elements.append(Paragraph("No category scores available.", normal_style))
        
    elements.append(Spacer(1, 20))
    
    # 4. Actionable Recommendations
    elements.append(Paragraph("Actionable Recommendations", heading2_style))
    recommendations = report_data.get("recommendations", [])
    
    if recommendations:
        rec_data = [["Category", "Title", "Priority", "Status"]]
        for rec in recommendations:
            # Handle both dict and Pydantic model
            if isinstance(rec, dict):
                rec_data.append([
                    rec.get("category", "N/A"),
                    rec.get("title", "N/A"),
                    rec.get("priority", "N/A"),
                    rec.get("status", "Open")
                ])
            else:
                rec_data.append([
                    getattr(rec, "category", "N/A"),
                    getattr(rec, "title", "N/A"),
                    getattr(rec, "priority", "N/A"),
                    getattr(rec, "status", "Open")
                ])
                
        rec_table = Table(rec_data, colWidths=[100, 250, 80, 80])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('WORDWRAP', (0, 0), (-1, -1), True)
        ]))
        elements.append(rec_table)
        
        # Detailed descriptions
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Recommendation Details:", styles["Heading3"]))
        for rec in recommendations:
            cat = rec.get("category", "N/A") if isinstance(rec, dict) else getattr(rec, "category", "N/A")
            title = rec.get("title", "N/A") if isinstance(rec, dict) else getattr(rec, "title", "N/A")
            desc = rec.get("description", "N/A") if isinstance(rec, dict) else getattr(rec, "description", "N/A")
            
            elements.append(Paragraph(f"<b>[{cat}] {title}</b>", normal_style))
            elements.append(Paragraph(desc, normal_style))
            elements.append(Spacer(1, 10))
            
    else:
        elements.append(Paragraph("No recommendations found.", normal_style))

    # 5. Report Footer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Thank you for using Website Auditor.", normal_style))
    
    # Build the PDF
    doc.build(elements)
    return output_path
