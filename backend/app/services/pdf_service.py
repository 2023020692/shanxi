from pathlib import Path
import datetime


def generate_pdf_report(output_path: str, title: str, stats: dict = None) -> str:
    """Generate a PDF report using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import HRFlowable
    from reportlab.platypus import Image as RLImage
    from io import BytesIO
    from PIL import Image as PILImage, ImageDraw

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
    )
    story.append(Paragraph(title, title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.5 * cm))

    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"生成时间: {date_str}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    if stats:
        story.append(Paragraph("数据统计", styles["Heading2"]))
        table_data = [["指标", "值"]]
        for k, v in stats.items():
            table_data.append([str(k), str(v)])
        t = Table(table_data, colWidths=[8 * cm, 8 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a6496")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5 * cm))

    # Placeholder map image (colored rectangle)
    img_buf = BytesIO()
    pil_img = PILImage.new("RGB", (500, 300), color=(200, 230, 200))
    draw = ImageDraw.Draw(pil_img)
    draw.rectangle([10, 10, 490, 290], outline=(100, 150, 100), width=3)
    draw.text((200, 130), "地图示意图", fill=(80, 120, 80))
    pil_img.save(img_buf, format="PNG")
    img_buf.seek(0)

    rl_image = RLImage(img_buf, width=14 * cm, height=8 * cm)
    story.append(Paragraph("地图概览", styles["Heading2"]))
    story.append(rl_image)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("备注: 本报告由山西省 WebGIS 平台自动生成。", styles["Normal"]))

    doc.build(story)
    return str(output)
