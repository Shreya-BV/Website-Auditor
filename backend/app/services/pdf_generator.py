import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

class FooterDocTemplate(SimpleDocTemplate):
    def __init__(self, filename, **kw):
        self.website_url = kw.pop('website_url', '')
        super().__init__(filename, **kw)

    def build(self, flowables, **kwargs):
        self._calc()
        super().build(flowables, onFirstPage=self._header_footer, onLaterPages=self._header_footer, **kwargs)

    def _header_footer(self, canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.HexColor("#7F8C8D"))
        # Footer
        footer_text = f"Website Audit Report - {self.website_url}" if self.website_url else "Website Audit Report"
        canvas_obj.drawString(doc.leftMargin, 0.5 * inch, footer_text)
        page_num = f"Page {doc.page}"
        canvas_obj.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.5 * inch, page_num)
        canvas_obj.restoreState()


def get_priority_color(priority):
    if not priority: return colors.HexColor("#7F8C8D")
    p = priority.lower()
    if p == "critical": return colors.HexColor("#E74C3C")
    if p == "high": return colors.HexColor("#E67E22")
    if p == "medium": return colors.HexColor("#F1C40F")
    if p == "low": return colors.HexColor("#3498DB")
    return colors.HexColor("#7F8C8D")

def get_grade_color(score):
    if score >= 90: return colors.HexColor("#2ECC71") # A
    if score >= 80: return colors.HexColor("#3498DB") # B
    if score >= 70: return colors.HexColor("#F1C40F") # C
    if score >= 50: return colors.HexColor("#E67E22") # D
    return colors.HexColor("#E74C3C") # F


def generate_audit_pdf(report_data: dict, output_path: str):
    """
    Generate a highly professional enterprise PDF report for the website audit using reportlab.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    website_url = report_data.get("website_url", "N/A")
    doc = FooterDocTemplate(output_path, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40,
                            website_url=website_url)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    h1_style = ParagraphStyle(
        name="H1Style", parent=styles["Heading1"], fontSize=26,
        textColor=colors.HexColor("#2C3E50"), spaceAfter=20, alignment=1
    )
    h2_style = ParagraphStyle(
        name="H2Style", parent=styles["Heading2"], fontSize=18,
        textColor=colors.HexColor("#2980B9"), spaceBefore=20, spaceAfter=15,
    )
    h3_style = ParagraphStyle(
        name="H3Style", parent=styles["Heading3"], fontSize=14,
        textColor=colors.HexColor("#34495E"), spaceBefore=15, spaceAfter=10,
    )
    normal_style = styles["Normal"]
    normal_style.fontSize = 10
    normal_style.textColor = colors.HexColor("#333333")
    normal_style.leading = 14

    elements = []
    
    # --- 1. COVER PAGE ---
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("Enterprise Website Audit", h1_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>Website:</b> {website_url}", h1_style))
    elements.append(Spacer(1, 40))
    
    date_str = report_data.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M') if isinstance(report_data.get('created_at'), datetime) else report_data.get('created_at', 'N/A')
    
    cover_info = [
        ["Report ID:", str(report_data.get('_id', 'N/A'))],
        ["Scan Date:", date_str],
        ["User Name:", report_data.get('user_name', 'N/A')],
        ["User Email:", report_data.get('email', 'N/A')],
        ["Website Title:", report_data.get('website_title', 'N/A')]
    ]
    t_cover = Table(cover_info, colWidths=[150, 250])
    t_cover.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#34495E")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_cover)
    elements.append(PageBreak())
    
    # --- 2. EXECUTIVE SUMMARY ---
    elements.append(Paragraph("Executive Summary", h2_style))
    score = report_data.get('audit_score', 0)
    grade = report_data.get('grade', 'C')
    target = report_data.get('target_score', '85+')
    
    summary_text = f"This report provides a comprehensive enterprise-grade analysis of {website_url}. " \
                   f"The overall audit score is <b>{score} out of 100</b> (Grade {grade}). " \
                   f"A total of {report_data.get('issues_found', 0)} issues were identified that require attention. " \
                   f"The target score for industry benchmark is {target}."
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 20))

    # --- 3. OVERALL SCORE ---
    elements.append(Paragraph("Overall Score", h3_style))
    score_data = [
        ["Overall Score", "Grade", "Benchmark", "Target Score"],
        [f"{score} / 100", grade, report_data.get("benchmark", "Average"), target]
    ]
    t_score = Table(score_data, colWidths=[130, 130, 130, 130])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('TEXTCOLOR', (0, 1), (0, 1), get_grade_color(score)),
        ('TEXTCOLOR', (1, 1), (1, 1), get_grade_color(score)),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 12),
        ('TOPPADDING', (0, 1), (-1, 1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
    ]))
    elements.append(t_score)
    elements.append(Spacer(1, 30))

    # --- 4. FIVE PILLARS ---
    elements.append(Paragraph("Category Performance (Five Pillars)", h2_style))
    category_scores = report_data.get("category_scores", {})
    pillar_details = report_data.get("pillar_details", {})
    
    if category_scores:
        cat_data = [["Pillar", "Score", "Passed", "Failed"]]
        for cat, c_score in category_scores.items():
            details = pillar_details.get(cat, {})
            passed = details.get("passed_checks", "-") if isinstance(details, dict) else getattr(details, "passed_checks", "-")
            failed = details.get("failed_checks", "-") if isinstance(details, dict) else getattr(details, "failed_checks", "-")
            cat_data.append([cat.replace("_", " ").title(), str(c_score), str(passed), str(failed)])
            
        t_cat = Table(cat_data, colWidths=[200, 100, 100, 100])
        t_cat.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
        ]))
        elements.append(t_cat)
    else:
        elements.append(Paragraph("No category scores available.", normal_style))
    
    elements.append(PageBreak())

    # --- 5. DETAILED FINDINGS & 6. RECOMMENDATIONS ---
    elements.append(Paragraph("Detailed Findings & Recommendations", h2_style))
    recommendations = report_data.get("recommendations", [])
    
    if recommendations:
        for rec in recommendations:
            cat = rec.get("category", "N/A") if isinstance(rec, dict) else getattr(rec, "category", "N/A")
            title = rec.get("title", "N/A") if isinstance(rec, dict) else getattr(rec, "title", "N/A")
            desc = rec.get("description", "N/A") if isinstance(rec, dict) else getattr(rec, "description", "N/A")
            priority = rec.get("priority", "N/A") if isinstance(rec, dict) else getattr(rec, "priority", "N/A")
            b_impact = rec.get("business_impact", "N/A") if isinstance(rec, dict) else getattr(rec, "business_impact", "N/A")
            steps = rec.get("implementation_steps", "N/A") if isinstance(rec, dict) else getattr(rec, "implementation_steps", "N/A")
            est_time = rec.get("estimated_time", "N/A") if isinstance(rec, dict) else getattr(rec, "estimated_time", "N/A")
            exp_score = rec.get("expected_score_improvement", "N/A") if isinstance(rec, dict) else getattr(rec, "expected_score_improvement", "N/A")

            # Box it in a table
            rec_block = [
                [Paragraph(f"<b>Issue:</b> {title} ({cat})", h3_style), Paragraph(f"<b>Priority: {priority}</b>", normal_style)],
                [Paragraph("<b>Current Problem:</b>", normal_style), Paragraph(desc, normal_style)],
                [Paragraph("<b>Business Impact:</b>", normal_style), Paragraph(str(b_impact), normal_style)],
                [Paragraph("<b>How to Fix:</b>", normal_style), Paragraph(str(steps), normal_style)],
                [Paragraph("<b>Estimated Time:</b>", normal_style), Paragraph(str(est_time), normal_style)],
                [Paragraph("<b>Expected Score Impact:</b>", normal_style), Paragraph(f"+{exp_score}", normal_style)]
            ]
            t_rec = Table(rec_block, colWidths=[150, 350])
            t_rec.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#ECF0F1")),
                ('TEXTCOLOR', (1, 0), (1, 0), get_priority_color(priority)),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
            ]))
            elements.append(KeepTogether(t_rec))
            elements.append(Spacer(1, 15))
    else:
        elements.append(Paragraph("No specific recommendations found. Great job!", normal_style))

    elements.append(PageBreak())

    # --- 7. TECHNOLOGY DETECTION ---
    elements.append(Paragraph("Technology Detection", h2_style))
    techs = report_data.get("technology_detections", [])
    if techs:
        tech_data = [["Technology", "Status", "Confidence"]]
        for t in techs:
            name = t.get("name", "Unknown") if isinstance(t, dict) else getattr(t, "name", "Unknown")
            found = t.get("found", False) if isinstance(t, dict) else getattr(t, "found", False)
            conf = t.get("confidence", "N/A") if isinstance(t, dict) else getattr(t, "confidence", "N/A")
            status = "Found" if found else "Not Found"
            tech_data.append([name, status, f"{conf}%" if conf != "N/A" else "N/A"])
        
        t_tech = Table(tech_data, colWidths=[200, 150, 150])
        t_tech.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
        ]))
        elements.append(t_tech)
    else:
        elements.append(Paragraph("No technology detection data available.", normal_style))

    elements.append(Spacer(1, 20))

    # --- 8. PERFORMANCE SUMMARY ---
    elements.append(Paragraph("Performance Summary", h2_style))
    perf = report_data.get("performance_metrics", {})
    if perf:
        perf_data = [
            ["Metric", "Time (ms)"],
        ]
        for key, val in (perf.items() if isinstance(perf, dict) else perf.__dict__.items()):
            if val is not None and key != "rendering_method":
                perf_data.append([key.replace("_", " ").title(), str(val)])
        if "rendering_method" in (perf if isinstance(perf, dict) else perf.__dict__):
            rm = perf.get("rendering_method") if isinstance(perf, dict) else getattr(perf, "rendering_method")
            perf_data.append(["Rendering Method", str(rm)])
            
        t_perf = Table(perf_data, colWidths=[250, 250])
        t_perf.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
        ]))
        elements.append(t_perf)
    else:
        elements.append(Paragraph("No performance metrics available.", normal_style))

    elements.append(Spacer(1, 30))

    # --- 9. FINAL CONCLUSION ---
    elements.append(Paragraph("Final Conclusion", h2_style))
    conclusion_text = f"The website {website_url} currently scores a {score}/100. "
    if score >= 80:
        conclusion_text += "This is an excellent result, indicating high maturity in digital presence. Focus on minor optimizations."
    elif score >= 50:
        conclusion_text += "This indicates average maturity. Implementing the recommendations provided in this report, particularly the high-priority ones, will significantly improve marketing impact, SEO, and conversion rates."
    else:
        conclusion_text += "This indicates low digital maturity. Urgent attention is required on critical and high-priority recommendations to avoid severe negative impacts on traffic and conversions."
    elements.append(Paragraph(conclusion_text, normal_style))
    
    # Build the PDF
    doc.build(elements)
    return output_path
