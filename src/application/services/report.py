from datetime import datetime, timedelta
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from domain.datasets.aggregate import Dataset

# --- DSFR & Design System Colors ---
DSFR_BLUE_FRANCE = colors.Color(0, 0, 0.569)  # #000091
DSFR_RED_MARIANNE = colors.Color(0.882, 0, 0.059)  # #E1000F
DSFR_GREY_975 = colors.Color(0.975, 0.975, 0.975)  # #F5F5F5
DSFR_GREY_900 = colors.Color(0.9, 0.9, 0.9)  # #E5E5E5
DSFR_BLUE_LIGHT = colors.Color(0.92, 0.92, 0.96)  # Light blue background
TEXT_COLOR = colors.Color(0.1, 0.1, 0.1)


class AuditReportTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        self.pagesize = A4

        # Define Frames
        # Margin: 2cm
        frame_width = A4[0] - 4 * cm
        frame_height = A4[1] - 5 * cm  # Leave space for header/footer

        self.main_frame = Frame(2 * cm, 2.5 * cm, frame_width, frame_height, id="main_frame", showBoundary=0)

        self.addPageTemplates(
            [
                PageTemplate(id="FirstPage", frames=[self.main_frame], onPage=self.header_footer),
                PageTemplate(id="LaterPages", frames=[self.main_frame], onPage=self.header_footer),
            ]
        )

    def header_footer(self, canvas: canvas.Canvas, doc):
        canvas.saveState()

        # --- Header ---
        # Blue stripe at the top
        canvas.setFillColor(DSFR_BLUE_FRANCE)
        canvas.rect(0, A4[1] - 2 * cm, A4[0], 2 * cm, fill=1, stroke=0)

        # Title in Header
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawString(2 * cm, A4[1] - 1.3 * cm, "OPEN DATA MONITORING")

        canvas.setFont("Helvetica", 12)
        canvas.drawString(2 * cm, A4[1] - 1.8 * cm, "Rapport d'Audit Qualité")

        # Subtitle in Header (Right side)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.3 * cm, "AUDIT REPORT")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.8 * cm, "OPEN DATA QUALITY")

        # --- Footer ---
        # Page Number
        canvas.setFillColor(TEXT_COLOR)
        canvas.setFont("Helvetica", 9)
        page_num_text = f"Page {doc.page}"
        canvas.drawRightString(A4[0] - 2 * cm, 1.5 * cm, page_num_text)

        # Date and App Name
        date_str = datetime.now().strftime("%d/%m/%Y")
        canvas.drawString(2 * cm, 1.5 * cm, f"Généré le {date_str} par Open Data Monitoring")

        # Separator Line
        canvas.setStrokeColor(DSFR_GREY_900)
        canvas.line(2 * cm, 2 * cm, A4[0] - 2 * cm, 2 * cm)

        canvas.restoreState()


class ReportGenerator:
    def _get_styles(self):
        styles = getSampleStyleSheet()

        # Custom styles
        styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=24,
                leading=28,
                textColor=DSFR_BLUE_FRANCE,
                spaceAfter=12,
                alignment=TA_LEFT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=20,
                textColor=DSFR_BLUE_FRANCE,
                spaceBefore=20,
                spaceAfter=10,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SubSectionHeader",
                parent=styles["Heading3"],
                fontSize=12,
                fontName="Helvetica-Bold",
                textColor=TEXT_COLOR,
                spaceBefore=10,
                spaceAfter=5,
            )
        )

        styles.add(
            ParagraphStyle(
                name="NormalText",
                parent=styles["Normal"],
                fontSize=10,
                leading=14,
                textColor=TEXT_COLOR,
                alignment=TA_LEFT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SmallText",
                parent=styles["Normal"],
                fontSize=8,
                leading=10,
                textColor=colors.gray,
            )
        )

        styles.add(
            ParagraphStyle(
                name="MetadataLabel",
                parent=styles["Normal"],
                fontSize=9,
                textColor=colors.gray,
            )
        )

        styles.add(
            ParagraphStyle(
                name="MetadataValue",
                parent=styles["Normal"],
                fontSize=10,
                textColor=TEXT_COLOR,
                fontName="Helvetica-Bold",
            )
        )

        styles.add(
            ParagraphStyle(
                name="ScoreValue",
                parent=styles["Normal"],
                fontSize=32,
                leading=40,
                fontName="Helvetica-Bold",
                textColor=colors.white,
                alignment=TA_CENTER,
            )
        )

        styles.add(
            ParagraphStyle(
                name="StatValue",
                parent=styles["Normal"],
                fontSize=20,
                fontName="Helvetica-Bold",
                textColor=DSFR_BLUE_FRANCE,
                alignment=TA_CENTER,
            )
        )

        styles.add(
            ParagraphStyle(
                name="StatLabel", parent=styles["Normal"], fontSize=10, textColor=colors.gray, alignment=TA_CENTER
            )
        )

        return styles

    def generate_audit_report(self, dataset: Dataset) -> BytesIO:
        """Main entry point to generate the PDF audit report."""
        buffer = BytesIO()
        doc = AuditReportTemplate(buffer)
        styles = self._get_styles()
        story = []

        # 1. Title & Discovery Info
        self._add_report_title(story, dataset, styles)
        self._add_metadata_card(story, dataset, styles)

        # 2. Quality Banner
        results = dataset.quality.evaluation_results if dataset.quality else {}
        self._add_score_banner(story, results, styles)

        # 3. Stats & Compliance
        self._add_usage_statistics(story, dataset, styles)
        self._add_basic_indicators(story, dataset, styles)

        # 4. Deep Analysis
        if results.get("criteria_scores"):
            self._add_criteria_analysis(story, results["criteria_scores"], styles)

        if results.get("suggestions"):
            self._add_improvement_suggestions(story, results["suggestions"], styles)

        # 5. Business KPIs (Discoverability & Impact)
        if dataset.quality and dataset.quality.discoverability:
            self._add_business_kpis(story, dataset.quality, styles)

        # 6. Miscellaneous
        self._add_additional_indicators(story, results, styles)

        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_impact_report(self, dataset: Dataset) -> BytesIO:
        """Entry point for a business-oriented Dataset Impact Report."""
        buffer = BytesIO()
        doc = AuditReportTemplate(buffer)  # Reuse template for consistent header/footer
        styles = self._get_styles()
        story = []

        # 1. Title & Identity
        self._add_report_title(story, dataset, styles, subtitle="RAPPORT D'IMPACT BUSINESS")
        self._add_metadata_card(story, dataset, styles)

        # 2. Key Impact KPIs
        impact_score = dataset.quality.health_engagement_score if dataset.quality else 0
        self._add_impact_score_banner(story, impact_score, styles)

        # 3. Consumption vs Notoriety
        self._add_impact_vitals(story, dataset, styles)

        # 4. Temporal Trends (Evolution)
        self._add_evolution_trends(story, dataset, styles)

        # 5. Engagement & Reuses
        self._add_engagement_details(story, dataset, styles)

        # 6. Actionable recommendations
        if dataset.quality and dataset.quality.evaluation_results.get("suggestions"):
            self._add_improvement_suggestions(story, dataset.quality.evaluation_results["suggestions"], styles)

        doc.build(story)
        buffer.seek(0)
        return buffer

    def _add_report_title(self, story: list, dataset: Dataset, styles: Any, subtitle: str = None):
        """Adds the main dataset title."""
        title_text = dataset.title or str(dataset.slug)
        story.append(Paragraph(title_text, styles["ReportTitle"]))
        if subtitle:
            story.append(Paragraph(subtitle, styles["SubSectionHeader"]))
        story.append(Spacer(1, 0.5 * cm))

    def _add_metadata_card(self, story: list, dataset: Dataset, styles: Any):
        """Adds dataset identification info in a colored block."""
        meta_data = [
            [
                Paragraph("Identifiant (Slug)", styles["MetadataLabel"]),
                Paragraph(str(dataset.slug), styles["MetadataValue"]),
            ],
            [
                Paragraph("Producteur", styles["MetadataLabel"]),
                Paragraph(dataset.publisher or "Inconnu", styles["MetadataValue"]),
            ],
            [
                Paragraph("Page source", styles["MetadataLabel"]),
                Paragraph(f'<a href="{dataset.page}" color="blue">{dataset.page}</a>', styles["NormalText"]),
            ],
        ]

        meta_table = Table(meta_data, colWidths=[4 * cm, 12 * cm])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), DSFR_BLUE_LIGHT),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 10),
                    ("Grid", (0, 0), (-1, -1), 0.5, colors.white),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 0.8 * cm))

    def _add_score_banner(self, story: list, results: dict, styles: Any):
        """Adds the large color-coded score box."""
        score = results.get("overall_score")
        if score is None:
            return

        level_map = [
            (85, "Excellente", colors.green),
            (70, "Bonne", colors.green),
            (50, "Satisfaisante", colors.orange),
            (0, "À améliorer", colors.red),
        ]
        level_label, bg_color = next((label, color) for limit, label, color in level_map if score >= limit)

        score_data = [
            [
                Paragraph(f"Score Global: {level_label}", styles["MetadataLabel"]),
                Paragraph(f"{round(score)}/100", styles["ScoreValue"]),
            ]
        ]
        score_table = Table(score_data, colWidths=[16 * cm])
        score_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 15),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ]
            )
        )
        story.append(score_table)
        story.append(Spacer(1, 1 * cm))

    def _add_usage_statistics(self, story: list, dataset: Dataset, styles: Any):
        """Adds usage counts (downloads, API calls)."""
        story.append(Paragraph("Statistiques d'utilisation", styles["SectionHeader"]))
        usage_data = [
            [
                Paragraph(f"{dataset.downloads_count or 0:,}", styles["StatValue"]),
                Paragraph(f"{dataset.api_calls_count or 0:,}", styles["StatValue"]),
            ],
            [Paragraph("Téléchargements", styles["StatLabel"]), Paragraph("Appels API", styles["StatLabel"])],
        ]
        usage_table = Table(usage_data, colWidths=[8 * cm, 8 * cm])
        usage_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
                    ("TOPPADDING", (0, 1), (-1, 1), 0),
                ]
            )
        )
        story.append(usage_table)
        story.append(Spacer(1, 0.5 * cm))

    def _add_basic_indicators(self, story: list, dataset: Dataset, styles: Any):
        """Adds basic indicators like description presence."""
        story.append(Paragraph("Indicateurs de base", styles["SectionHeader"]))
        has_desc = "Oui" if dataset.quality and dataset.quality.has_description else "Non"
        slug_valid = "Oui" if dataset.quality and dataset.quality.is_slug_valid else "Non"
        basic_metrics = [["Indicateur", "État"], ["Description présente", has_desc], ["Slug conforme", slug_valid]]
        bt = Table(basic_metrics, colWidths=[10 * cm, 6 * cm], hAlign="LEFT")
        bt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), DSFR_GREY_900),
                    ("GRID", (0, 0), (-1, -1), 0.5, DSFR_GREY_900),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(bt)
        story.append(Spacer(1, 1 * cm))

    def _add_criteria_analysis(self, story: list, criteria_scores: dict, styles: Any):
        """Adds grouped criteria breakdown."""
        story.append(Paragraph("Analyse par critères", styles["SectionHeader"]))
        categories = {"administrative": "Administration", "descriptive": "Description", "geotemporal": "Géo-temporel"}

        for cat_id, cat_label in categories.items():
            cat_criteria = {k: v for k, v in criteria_scores.items() if v.get("category") == cat_id}
            if not cat_criteria:
                continue
            story.append(Paragraph(cat_label.upper(), styles["SubSectionHeader"]))
            data = [["Critère", "Score", "Poids", "Problèmes"]]
            for key, val in cat_criteria.items():
                issues = "\n".join([f"• {i}" for i in val.get("issues", [])]) or "Aucun"
                data.append(
                    [
                        val.get("criterion", key),
                        f"{round(val.get('score'))}/100",
                        f"{round(val.get('weight', 0) * 100)}%",
                        Paragraph(issues, styles["NormalText"]),
                    ]
                )
            ct = Table(data, colWidths=[4 * cm, 2 * cm, 2 * cm, 8 * cm])
            ct.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), DSFR_BLUE_LIGHT),
                        ("TEXTCOLOR", (0, 0), (-1, 0), DSFR_BLUE_FRANCE),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, DSFR_GREY_900),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ]
                )
            )
            story.append(ct)
            story.append(Spacer(1, 0.5 * cm))

    def _add_improvement_suggestions(self, story: list, suggestions: list, styles: Any):
        """Adds suggestion cards."""
        story.append(Paragraph("Suggestions d'amélioration", styles["SectionHeader"]))
        for s in suggestions:
            if isinstance(s, dict):
                prio, field, val, reason = (
                    s.get("priority", "medium").upper(),
                    s.get("field", "Global"),
                    s.get("suggested_value", "-"),
                    s.get("reason", ""),
                )
            else:
                prio, field, val, reason = "MEDIUM", "Général", str(s), "Amélioration suggérée par l'audit."
            card_data = [
                [
                    Paragraph(f"<b>{field}</b>", styles["NormalText"]),
                    Paragraph(f"Priorité: {prio}", styles["SmallText"]),
                ],
                [Paragraph(f"<b>Proposé:</b> {val}", styles["NormalText"]), ""],
                [Paragraph(f"<i>{reason}</i>", styles["SmallText"]), ""],
            ]
            card = Table(card_data, colWidths=[12 * cm, 4 * cm])
            card.setStyle(
                TableStyle(
                    [
                        ("LINEBEFORE", (0, 0), (0, -1), 3, DSFR_BLUE_FRANCE),
                        ("BACKGROUND", (0, 0), (-1, -1), DSFR_GREY_975),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("SPAN", (0, 1), (1, 1)),
                        ("SPAN", (0, 2), (1, 2)),
                    ]
                )
            )
            story.append(KeepTogether(card))
            story.append(Spacer(1, 0.4 * cm))

    def _add_business_kpis(self, story: list, quality: Any, styles: Any):
        """Adds visual represention of Business KPIs."""
        story.append(Paragraph("Indicateurs Business & Gouvernance", styles["SectionHeader"]))

        # Discoverability
        disc = quality.discoverability
        story.append(Paragraph("DÉCOUVRABILITÉ", styles["SubSectionHeader"]))
        disc_data = [
            ["SEO (Titre)", f"{round(disc.seo_score)}/100"],
            ["Complétude DCAT", f"{round(disc.dcat_completeness_score)}/100"],
            ["Fraîcheur", f"{round(disc.freshness_score)}/100"],
            [
                "Qualité Sémantique",
                f"{round(disc.semantic_quality_score or 0)}/100" if disc.semantic_quality_score else "N/A",
            ],
        ]
        dt = Table(disc_data, colWidths=[8 * cm, 8 * cm])
        dt.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, DSFR_GREY_900),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("BACKGROUND", (1, 0), (1, -1), DSFR_BLUE_LIGHT),
                ]
            )
        )
        story.append(dt)
        story.append(Spacer(1, 0.5 * cm))

        # Impact
        imp = quality.impact
        story.append(Paragraph("IMPACT & ENGAGEMENT", styles["SubSectionHeader"]))
        imp_data = [
            ["Taux d'engagement", f"{imp.engagement_rate:.2%}"],
            ["Intensité d'usage (API)", f"{imp.usage_intensity:.2%}"],
            ["Score de popularité", f"{round(imp.popularity_score)}/100"],
            ["Score Global Impact", f"<b>{round(imp.overall_impact_score)}/100</b>"],
        ]
        it = Table(imp_data, colWidths=[8 * cm, 8 * cm])
        it.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, DSFR_GREY_900),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("BACKGROUND", (1, 3), (1, 3), DSFR_BLUE_LIGHT),
                ]
            )
        )
        story.append(it)
        story.append(Spacer(1, 1 * cm))

    def _add_additional_indicators(self, story: list, results: dict, styles: Any):
        """Adds other indicators at the end."""
        ignore_keys = ["score", "suggestions", "overall_score", "criteria_scores", "evaluated_at"]
        other_data = [
            [Paragraph(k.replace("_", " ").capitalize(), styles["NormalText"]), Paragraph(str(v), styles["NormalText"])]
            for k, v in results.items()
            if k not in ignore_keys
        ]
        if other_data:
            story.append(Paragraph("Autres indicateurs", styles["SectionHeader"]))
            ot = Table(other_data, colWidths=[6 * cm, 10 * cm], hAlign="LEFT")
            ot.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, DSFR_GREY_900),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(ot)

    # --- Impact Specific Methods ---

    def _add_impact_score_banner(self, story: list, score: float, styles: Any):
        """Large color banner for impact score."""
        level_map = [
            (80, "Impact Critique (Élite)", colors.gold),
            (60, "Impact Majeur", colors.green),
            (30, "Impact Modéré", colors.orange),
            (0, "Impact Faible", colors.grey),
        ]
        level_label, bg_color = next((label, color) for limit, label, color in level_map if score >= limit)

        score_data = [
            [
                Paragraph("SCORE D'IMPACT BUSINESS", styles["MetadataLabel"]),
                Paragraph(f"{round(score)}/100", styles["ScoreValue"]),
                Paragraph(level_label, styles["MetadataLabel"]),
            ]
        ]
        score_table = Table(score_data, colWidths=[16 * cm])
        score_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 15),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ]
            )
        )
        story.append(score_table)
        story.append(Spacer(1, 1 * cm))

    def _add_impact_vitals(self, story: list, dataset: Dataset, styles: Any):
        """Highlights raw usage metrics."""
        story.append(Paragraph("Vitalité de l'Usage (Cumulé)", styles["SectionHeader"]))
        vitals_data = [
            [
                Paragraph(f"{dataset.views_count or 0:,}", styles["StatValue"]),
                Paragraph(f"{dataset.downloads_count or 0:,}", styles["StatValue"]),
                Paragraph(f"{dataset.api_calls_count or 0:,}", styles["StatValue"]),
            ],
            [
                Paragraph("Consultations", styles["StatLabel"]),
                Paragraph("Téléchargements", styles["StatLabel"]),
                Paragraph("Appels API", styles["StatLabel"]),
            ],
        ]
        v_table = Table(vitals_data, colWidths=[5.3 * cm] * 3)
        v_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(v_table)
        story.append(Spacer(1, 0.8 * cm))

    def _add_evolution_trends(self, story: list, dataset: Dataset, styles: Any):
        """Shows evolution of metrics over historical versions."""
        story.append(Paragraph("Dynamique Temporelle (Deltas)", styles["SectionHeader"]))

        # Filter versions with valid timestamps
        valid_versions = [v for v in dataset.versions if v.timestamp is not None]

        if len(valid_versions) < 2:
            story.append(Paragraph("Données historiques insuffisantes pour calculer les tendances.", styles["SmallText"]))
            story.append(Spacer(1, 0.5 * cm))
            return

        # Sort versions by timestamp
        versions = sorted(valid_versions, key=lambda v: v.timestamp)
        latest = versions[-1]
        
        # Calculate deltas for 7 days and 30 days if possible
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        def get_version_at_days_ago(days):
            target = now - timedelta(days=days)
            # Find the closest version that is at least 'days' old
            for v in reversed(versions):
                v_ts = v.timestamp if v.timestamp.tzinfo else v.timestamp.replace(tzinfo=timezone.utc)
                if v_ts <= target:
                    return v
            return versions[0]

        v_7d = get_version_at_days_ago(7)
        v_30d = get_version_at_days_ago(30)

        def get_delta_text(current, previous):
            if current is None or previous is None: return "N/A"
            delta = current - previous
            color = "green" if delta > 0 else "grey"
            return f'<font color="{color}">+{delta:,}</font>' if delta > 0 else f"{delta:,}"

        trends_data = [
            ["Metric", "Derniers 7 jours", "Derniers 30 jours"],
            ["Consultations", Paragraph(get_delta_text(latest.views_count, v_7d.views_count), styles["NormalText"]), Paragraph(get_delta_text(latest.views_count, v_30d.views_count), styles["NormalText"])],
            ["Téléchargements", Paragraph(get_delta_text(latest.downloads_count, v_7d.downloads_count), styles["NormalText"]), Paragraph(get_delta_text(latest.downloads_count, v_30d.downloads_count), styles["NormalText"])],
            ["Appels API", Paragraph(get_delta_text(latest.api_calls_count, v_7d.api_calls_count), styles["NormalText"]), Paragraph(get_delta_text(latest.api_calls_count, v_30d.api_calls_count), styles["NormalText"])]
        ]

        t_table = Table(trends_data, colWidths=[6 * cm, 5 * cm, 5 * cm])
        t_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), DSFR_BLUE_LIGHT),
            ('TEXTCOLOR', (0, 0), (-1, 0), DSFR_BLUE_FRANCE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, DSFR_GREY_900),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t_table)
        story.append(Spacer(1, 0.8 * cm))

    def _add_engagement_details(self, story: list, dataset: Dataset, styles: Any):
        """Focus on Reuses and Followers."""
        story.append(Paragraph("Notoriété & Appropriation", styles["SectionHeader"]))
        
        engagement_data = [
            [
                Paragraph(f"{dataset.reuses_count or 0}", styles["StatValue"]),
                Paragraph(f"{dataset.followers_count or 0}", styles["StatValue"]),
            ],
            [
                Paragraph("Réutilisations déclarées", styles["StatLabel"]),
                Paragraph("Abonnés (Followers)", styles["StatLabel"]),
            ],
        ]
        e_table = Table(engagement_data, colWidths=[8 * cm, 8 * cm])
        e_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(e_table)
        
        # Summary description
        engagement_rate = 0
        if dataset.views_count and dataset.views_count > 0:
            engagement_rate = (dataset.reuses_count or 0) / dataset.views_count
        
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph(f"Taux de transformation (vues -> réutilisation) : <b>{engagement_rate:.2%}</b>", styles["NormalText"]))
        story.append(Spacer(1, 0.8 * cm))
