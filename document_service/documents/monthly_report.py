from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_monthly_report_pdf(
    output_path: Path,
    data: dict,
) -> None:
    """
    Generate monthly business resolution report PDF.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "MonthlyReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=15,
    )

    heading_style = ParagraphStyle(
        "MonthlyReportHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "MonthlyReportBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
    )

    small_style = ParagraphStyle(
        "MonthlyReportSmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
    )

    def safe(value) -> str:
        if value is None:
            return "-"

        return escape(
            str(value)
        )

    def paragraph(
        value,
        style=body_style,
    ):
        return Paragraph(
            safe(value),
            style,
        )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=(
            f"Monthly Resolution Report "
            f"{data.get('month')}"
        ),
    )

    story = []

    # ======================================================
    # TITLE
    # ======================================================

    story.append(
        Paragraph(
            "Business Mention Resolution Platform",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"Monthly Resolution Report - "
            f"{safe(data.get('month'))}",
            heading_style,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    # ======================================================
    # SUMMARY
    # ======================================================

    story.append(
        Paragraph(
            "Monthly Summary",
            heading_style,
        )
    )

    summary_data = [
        [
            paragraph("Metric"),
            paragraph("Value"),
        ],
        [
            paragraph(
                "Mentions Processed"
            ),
            paragraph(
                data.get(
                    "mentions_processed"
                )
            ),
        ],
        [
            paragraph(
                "Automatically Resolved"
            ),
            paragraph(
                data.get(
                    "auto_resolved"
                )
            ),
        ],
        [
            paragraph(
                "Reviewer Approved"
            ),
            paragraph(
                data.get(
                    "reviewer_approved"
                )
            ),
        ],
        [
            paragraph(
                "Rejected"
            ),
            paragraph(
                data.get(
                    "rejected"
                )
            ),
        ],
        [
            paragraph(
                "Sent For Review"
            ),
            paragraph(
                data.get(
                    "sent_for_review"
                )
            ),
        ],
        [
            paragraph(
                "Match Rate"
            ),
            paragraph(
                f"{data.get('match_rate', 0):.2f}%"
            ),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            100 * mm,
            60 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#D9E2F3"
                    ),
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (0, -1),
                    colors.HexColor(
                        "#F2F2F2"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        summary_table
    )

    # ======================================================
    # REVIEW REASONS
    # ======================================================

    story.append(
        Paragraph(
            "Most Common Review Reasons",
            heading_style,
        )
    )

    review_reasons = data.get(
        "review_reasons",
        [],
    )

    if review_reasons:

        reason_rows = [
            [
                paragraph("Reason"),
                paragraph("Count"),
            ]
        ]

        for item in review_reasons:

            reason_rows.append(
                [
                    paragraph(
                        item.get("reason"),
                        small_style,
                    ),
                    paragraph(
                        item.get("count"),
                        small_style,
                    ),
                ]
            )

        reason_table = Table(
            reason_rows,
            colWidths=[
                130 * mm,
                30 * mm,
            ],
            repeatRows=1,
        )

        reason_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#D9E2F3"
                        ),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(
            reason_table
        )

    else:

        story.append(
            Paragraph(
                "No mentions were sent for review "
                "during this month.",
                body_style,
            )
        )

    # ======================================================
    # NOTES
    # ======================================================

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            (
                "Match Rate = "
                "(Automatically Resolved + "
                "Reviewer Approved) / "
                "Mentions Processed"
            ),
            small_style,
        )
    )

    story.append(
        Spacer(1, 6)
    )

    story.append(
        Paragraph(
            (
                "Generated by Business Mention "
                "Resolution Platform"
            ),
            small_style,
        )
    )

    document.build(
        story
    )