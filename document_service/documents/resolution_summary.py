from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_resolution_summary_pdf(
    output_path: Path,
    data: dict,
) -> None:
    """
    Generate a resolution summary PDF.

    The file is written to output_path.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ResolutionTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=15,
    )

    heading_style = ParagraphStyle(
        "ResolutionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "ResolutionBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
    )

    small_style = ParagraphStyle(
        "ResolutionSmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
    )

    def safe(value) -> str:
        if value is None:
            return "-"
        return escape(str(value))

    def paragraph(value, style=body_style):
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
        title="Business Resolution Summary",
    )

    story = []

    story.append(
        Paragraph(
            "Business Resolution Summary",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"Mention ID: {safe(data.get('mention_id'))}",
            body_style,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    # ------------------------------------------------------
    # Mention details
    # ------------------------------------------------------

    story.append(
        Paragraph(
            "Mention Details",
            heading_style,
        )
    )

    mention_data = [
        [
            paragraph("Mention"),
            paragraph(data.get("mention_text")),
        ],
        [
            paragraph("Source Type"),
            paragraph(data.get("source_type")),
        ],
        [
            paragraph("Source ID"),
            paragraph(data.get("source_id")),
        ],
        [
            paragraph("Source Text"),
            paragraph(data.get("source_text")),
        ],
    ]

    mention_table = Table(
        mention_data,
        colWidths=[
            42 * mm,
            125 * mm,
        ],
    )

    mention_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#EAEAEA"),
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

    story.append(mention_table)

    # ------------------------------------------------------
    # Resolution details
    # ------------------------------------------------------

    story.append(
        Paragraph(
            "Resolution",
            heading_style,
        )
    )

    resolution_data = [
        [
            paragraph("Status"),
            paragraph(
                data.get("resolution_status")
            ),
        ],
        [
            paragraph("Decision"),
            paragraph(
                data.get("decision")
            ),
        ],
        [
            paragraph("Confidence"),
            paragraph(
                data.get("confidence_score")
            ),
        ],
        [
            paragraph("Resolved Business ID"),
            paragraph(
                data.get("resolved_business_id")
            ),
        ],
    ]

    if data.get("reviewer_username"):

        resolution_data.append(
            [
                paragraph("Reviewer"),
                paragraph(
                    data.get(
                        "reviewer_username"
                    )
                ),
            ]
        )

    if data.get("reviewer_notes"):

        resolution_data.append(
            [
                paragraph("Reviewer Notes"),
                paragraph(
                    data.get(
                        "reviewer_notes"
                    )
                ),
            ]
        )

    resolution_table = Table(
        resolution_data,
        colWidths=[
            42 * mm,
            125 * mm,
        ],
    )

    resolution_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#EAEAEA"),
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

    story.append(resolution_table)

    # ------------------------------------------------------
    # Selected business
    # ------------------------------------------------------

    selected_business = data.get(
        "resolved_business"
    )

    if selected_business:

        story.append(
            Paragraph(
                "Resolved Business",
                heading_style,
            )
        )

        business_data = [
            [
                paragraph("Business ID"),
                paragraph(
                    selected_business.get(
                        "business_id"
                    )
                ),
            ],
            [
                paragraph("Name"),
                paragraph(
                    selected_business.get(
                        "name"
                    )
                ),
            ],
            [
                paragraph("Address"),
                paragraph(
                    selected_business.get(
                        "address"
                    )
                ),
            ],
            [
                paragraph("City"),
                paragraph(
                    selected_business.get(
                        "city"
                    )
                ),
            ],
            [
                paragraph("State"),
                paragraph(
                    selected_business.get(
                        "state"
                    )
                ),
            ],
            [
                paragraph("Postal Code"),
                paragraph(
                    selected_business.get(
                        "postal_code"
                    )
                ),
            ],
            [
                paragraph("Verified"),
                paragraph(
                    selected_business.get(
                        "is_verified"
                    )
                ),
            ],
        ]

        business_table = Table(
            business_data,
            colWidths=[
                42 * mm,
                125 * mm,
            ],
        )

        business_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor("#EAEAEA"),
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
            business_table
        )

    # ------------------------------------------------------
    # Candidate businesses
    # ------------------------------------------------------

    candidates = data.get(
        "candidates",
        [],
    )

    if candidates:

        story.append(
            Paragraph(
                "Candidates Considered",
                heading_style,
            )
        )

        candidate_rows = [
            [
                paragraph("Business"),
                paragraph("City"),
                paragraph("Score"),
                paragraph("Verified"),
                paragraph("Decision"),
            ]
        ]

        for candidate in candidates:

            candidate_rows.append(
                [
                    paragraph(
                        candidate.get(
                            "business_name"
                        ),
                        small_style,
                    ),
                    paragraph(
                        candidate.get(
                            "city"
                        ),
                        small_style,
                    ),
                    paragraph(
                        candidate.get(
                            "score"
                        ),
                        small_style,
                    ),
                    paragraph(
                        candidate.get(
                            "is_verified"
                        ),
                        small_style,
                    ),
                    paragraph(
                        candidate.get(
                            "decision"
                        ),
                        small_style,
                    ),
                ]
            )

        candidate_table = Table(
            candidate_rows,
            colWidths=[
                48 * mm,
                32 * mm,
                25 * mm,
                25 * mm,
                32 * mm,
            ],
            repeatRows=1,
        )

        candidate_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#D9E2F3"),
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
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(
            candidate_table
        )

    # ------------------------------------------------------
    # Notes
    # ------------------------------------------------------

    if data.get("decision_notes"):

        story.append(
            Paragraph(
                "Resolution Notes",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                safe(
                    data.get(
                        "decision_notes"
                    )
                ),
                body_style,
            )
        )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Generated by Business Mention Resolution Platform",
            small_style,
        )
    )

    document.build(story)