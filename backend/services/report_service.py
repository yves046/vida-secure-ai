import time

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def create_pdf_report(image_path):

    timestamp = int(time.time())

    pdf_name = f"rapport_{timestamp}.pdf"

    client_name = "VIDA DEMO"
    site_name = "Site Principal"
    zone_name = "Zone 1"
    license_id = "VIDA-DEMO"

    persons_count = 1
    intrusion_duration = 0

    incident_id = f"VIDA-{timestamp}"

    if persons_count >= 3:
        alert_level = "CRITIQUE"
    elif persons_count == 2:
        alert_level = "ÉLEVÉ"
    else:
        alert_level = "MODÉRÉ"

    pdf = SimpleDocTemplate(
        pdf_name,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<font size='22'><b>VIDA Secure AI</b></font>",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "<font color='grey'>Système intelligent de surveillance automatisée</font>",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    alert_table = Table(
        [["ALERTE SÉCURITÉ — INTRUSION DÉTECTÉE"]],
        colWidths=[535]
    )

    alert_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.red),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 16),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(alert_table)

    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            "<b>RÉSUMÉ DE L'INCIDENT</b>",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Client :</b> {client_name}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Site :</b> {site_name}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Zone :</b> {zone_name}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Licence :</b> {license_id}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    table = Table(
        [
            ["ÉLÉMENT", "VALEUR"],
            ["Date & heure", time.strftime("%Y-%m-%d %H:%M:%S")],
            ["Zone surveillée", zone_name],
            ["Niveau d'alerte", alert_level],
            ["ID Incident", incident_id],
            ["Durée intrusion", f"{intrusion_duration} secondes"],
            ["Nombre maximal de personnes", str(persons_count)],
        ],
        colWidths=[230, 305]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1F3A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "<b>ACTIONS AUTOMATIQUES EFFECTUÉES</b>",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph("✓ Capture photographique effectuée", styles["Normal"])
    )

    elements.append(
        Paragraph("✓ Enregistrement vidéo sauvegardé", styles["Normal"])
    )

    elements.append(
        Paragraph("✓ Notification e-mail envoyée", styles["Normal"])
    )

    elements.append(
        Paragraph("✓ Rapport d'incident généré", styles["Normal"])
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "<b>RECOMMANDATIONS VIDA</b>",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            "Nous recommandons de consulter les preuves numériques jointes afin de confirmer la nature exacte de l'événement détecté.",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            "En cas d'intrusion avérée, appliquez immédiatement les procédures de sécurité prévues par votre établissement.",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 40))

    footer_line = Table(
        [[""]],
        colWidths=[535],
        rowHeights=[1]
    )

    footer_line.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
    ]))

    elements.append(footer_line)

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "<font size='10' color='#666666'>"
            "VIDA Secure AI | Développé en Côte d'Ivoire | "
            "TOURE Yves – Ingénieur IA Sécurité"
            "</font>",
            styles["Normal"]
        )
    )

    print("AVANT PDF")

    pdf.build(elements)

    print("APRES PDF")
    print("PDF créé :", pdf_name)

    return pdf_name

