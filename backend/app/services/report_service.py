"""Report service — CSV and PDF export generation."""

import csv
import io
import logging
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from sqlalchemy.orm import Session

from app.models.query_log import QueryLog
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.services import analytics_service

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  CSV EXPORTS
# ═══════════════════════════════════════════════════════════════

def _date_filter(query, col, start: datetime | None, end: datetime | None):
    if start:
        query = query.filter(col >= start)
    if end:
        query = query.filter(col <= end)
    return query


def generate_query_log_csv(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> str:
    """Export query logs as CSV string."""
    q = db.query(QueryLog).order_by(QueryLog.created_at.desc())
    q = _date_filter(q, QueryLog.created_at, start_date, end_date)
    rows = q.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Date", "Query", "Response", "Confidence",
        "Sources", "Escalated", "Escalation Reason",
        "Response Time (ms)", "Has Evidence",
    ])

    for r in rows:
        writer.writerow([
            r.id,
            r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            r.query_text,
            r.response_text[:200] if r.response_text else "",
            round(r.confidence_score, 4) if r.confidence_score is not None else "",
            r.sources_count,
            "Yes" if r.escalated else "No",
            r.escalation_reason or "",
            r.response_time_ms or "",
            "Yes" if r.has_sufficient_evidence else "No",
        ])

    return output.getvalue()


def generate_escalation_csv(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> str:
    """Export escalated tickets as CSV string."""
    q = db.query(Ticket).order_by(Ticket.created_at.desc())
    q = _date_filter(q, Ticket.created_at, start_date, end_date)
    tickets = q.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Ticket ID", "Customer ID", "Status", "Priority",
        "Reason", "Agent ID", "Created", "Resolved",
        "Resolution Time (hrs)",
    ])

    for t in tickets:
        res_hours = ""
        if t.resolved_at and t.created_at:
            delta = (t.resolved_at - t.created_at).total_seconds() / 3600
            res_hours = round(delta, 1)

        writer.writerow([
            t.id,
            t.customer_id,
            t.status.value,
            t.priority.value,
            t.reason or "",
            t.assigned_agent_id or "",
            t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
            t.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if t.resolved_at else "",
            res_hours,
        ])

    return output.getvalue()


def generate_agent_performance_csv(db: Session) -> str:
    """Export agent performance metrics as CSV string."""
    agents = analytics_service.get_agent_performance(db)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Agent ID", "Agent Name", "Tickets Assigned",
        "Tickets Resolved", "Pending", "Avg Resolution (hrs)",
    ])

    for a in agents:
        writer.writerow([
            a["agent_id"],
            a["agent_name"],
            a["tickets_assigned"],
            a["tickets_resolved"],
            a["pending_tickets"],
            a["avg_resolution_time_hours"] or "",
        ])

    return output.getvalue()


def generate_analytics_summary_csv(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> str:
    """Export analytics overview + trends as CSV string."""
    overview = analytics_service.get_overview(db, start_date, end_date)
    perf = analytics_service.get_response_performance(db, start_date, end_date)
    esc = analytics_service.get_escalation_metrics(db, start_date, end_date)
    trends = analytics_service.get_query_trends(db, start_date, end_date, interval="day")

    output = io.StringIO()
    writer = csv.writer(output)

    # Section 1: Overview
    writer.writerow(["=== Overview Metrics ==="])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Queries", overview["total_queries"]])
    writer.writerow(["Total Conversations", overview["total_conversations"]])
    writer.writerow(["Total Escalations", overview["total_escalations"]])
    writer.writerow(["Escalation Rate (%)", overview["escalation_rate"]])
    writer.writerow(["Avg Confidence Score", overview["avg_confidence_score"]])
    writer.writerow(["Avg Response Time (ms)", overview["avg_response_time_ms"]])
    writer.writerow(["Queries with Evidence", overview["queries_with_evidence"]])
    writer.writerow(["Evidence Rate (%)", overview["evidence_rate"]])
    writer.writerow(["Active Tickets", overview["active_tickets"]])
    writer.writerow(["Resolved Tickets", overview["resolved_tickets"]])
    writer.writerow([])

    # Section 2: Confidence Distribution
    writer.writerow(["=== Confidence Distribution ==="])
    writer.writerow(["Level", "Count"])
    writer.writerow(["High (>=0.7)", perf["confidence_distribution"]["high"]])
    writer.writerow(["Medium (0.4-0.7)", perf["confidence_distribution"]["medium"]])
    writer.writerow(["Low (<0.4)", perf["confidence_distribution"]["low"]])
    writer.writerow([])

    # Section 3: Escalation Breakdown
    writer.writerow(["=== Escalation Breakdown ==="])
    writer.writerow(["Reason", "Count"])
    writer.writerow(["Low Confidence", esc["by_reason"]["low_confidence"]])
    writer.writerow(["Customer Requested", esc["by_reason"]["customer_requested"]])
    writer.writerow(["Other", esc["by_reason"]["other"]])
    writer.writerow([])

    # Section 4: Daily Trends
    if trends:
        writer.writerow(["=== Daily Query Trends ==="])
        writer.writerow(["Date", "Queries", "Escalations"])
        for t in trends:
            writer.writerow([t["date"], t["query_count"], t["escalation_count"]])

    return output.getvalue()


# ═══════════════════════════════════════════════════════════════
#  PDF GENERATION (ReportLab)
# ═══════════════════════════════════════════════════════════════

# Brand colours
_BRAND_ORANGE = colors.HexColor("#f97316")
_BRAND_DARK = colors.HexColor("#1a1a2e")
_HEADER_BG = colors.HexColor("#f1f5f9")
_ROW_ALT = colors.HexColor("#f8fafc")

_styles = getSampleStyleSheet()

_TITLE_STYLE = ParagraphStyle(
    "ReportTitle",
    parent=_styles["Title"],
    fontSize=26,
    textColor=_BRAND_DARK,
    spaceAfter=6,
)

_SUBTITLE_STYLE = ParagraphStyle(
    "ReportSubtitle",
    parent=_styles["Normal"],
    fontSize=12,
    textColor=colors.gray,
    spaceAfter=30,
)

_SECTION_STYLE = ParagraphStyle(
    "SectionHeading",
    parent=_styles["Heading2"],
    fontSize=16,
    textColor=_BRAND_DARK,
    spaceBefore=16,
    spaceAfter=10,
)

_BODY_STYLE = ParagraphStyle(
    "BodyText",
    parent=_styles["Normal"],
    fontSize=10,
    leading=14,
)


def _make_table(headers: list[str], rows: list[list], col_widths=None) -> Table:
    """Create a styled ReportLab table."""
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), _BRAND_ORANGE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # All cells
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]

    # Alternate row shading
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), _ROW_ALT))

    t.setStyle(TableStyle(style_cmds))
    return t


def generate_analytics_pdf(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> bytes:
    """Generate a multi-page analytics PDF report."""
    overview = analytics_service.get_overview(db, start_date, end_date)
    perf = analytics_service.get_response_performance(db, start_date, end_date)
    esc = analytics_service.get_escalation_metrics(db, start_date, end_date)
    agents = analytics_service.get_agent_performance(db)
    top_q = analytics_service.get_top_queries(db, limit=15)
    trends = analytics_service.get_query_trends(db, start_date, end_date, interval="day")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=30 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    elements = []
    page_width = A4[0] - 40 * mm  # usable width

    # ── Cover / Title ─────────────────────────────────────
    elements.append(Spacer(1, 60))
    elements.append(Paragraph("SupportIQ Analytics Report", _TITLE_STYLE))

    date_range_str = "All Time"
    if start_date and end_date:
        date_range_str = f"{start_date.strftime('%d %b %Y')} — {end_date.strftime('%d %b %Y')}"
    elif start_date:
        date_range_str = f"From {start_date.strftime('%d %b %Y')}"
    elif end_date:
        date_range_str = f"Until {end_date.strftime('%d %b %Y')}"

    elements.append(Paragraph(
        f"Period: {date_range_str}<br/>Generated: {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}",
        _SUBTITLE_STYLE,
    ))

    # ── Overview Metrics ──────────────────────────────────
    elements.append(Paragraph("Overview Metrics", _SECTION_STYLE))
    overview_rows = [
        ["Total Queries", str(overview["total_queries"])],
        ["Total Conversations", str(overview["total_conversations"])],
        ["Total Escalations", str(overview["total_escalations"])],
        ["Escalation Rate", f"{overview['escalation_rate']}%"],
        ["Avg Confidence Score", f"{round(overview['avg_confidence_score'] * 100, 1)}%"],
        ["Avg Response Time", f"{overview['avg_response_time_ms']} ms"],
        ["Queries with Evidence", str(overview["queries_with_evidence"])],
        ["Evidence Rate", f"{overview['evidence_rate']}%"],
        ["Active Tickets", str(overview["active_tickets"])],
        ["Resolved Tickets", str(overview["resolved_tickets"])],
    ]
    elements.append(_make_table(
        ["Metric", "Value"],
        overview_rows,
        col_widths=[page_width * 0.55, page_width * 0.45],
    ))

    # ── Confidence Distribution ───────────────────────────
    elements.append(Paragraph("Response Performance", _SECTION_STYLE))
    dist = perf["confidence_distribution"]
    perf_rows = [
        ["Avg Confidence", f"{round(perf['avg_confidence'] * 100, 1)}%"],
        ["Avg Response Time", f"{perf['avg_response_time_ms']} ms"],
        ["Avg Sources / Response", str(perf["avg_sources_per_response"])],
        ["High Confidence (≥0.7)", str(dist["high"])],
        ["Medium Confidence (0.4–0.7)", str(dist["medium"])],
        ["Low Confidence (<0.4)", str(dist["low"])],
    ]
    elements.append(_make_table(
        ["Metric", "Value"],
        perf_rows,
        col_widths=[page_width * 0.55, page_width * 0.45],
    ))

    # ── Escalation Breakdown ──────────────────────────────
    elements.append(Paragraph("Escalation Report", _SECTION_STYLE))
    esc_summary_rows = [
        ["Total Escalations", str(esc["total_escalations"])],
        ["Escalation Rate", f"{esc['escalation_rate']}%"],
        ["Low Confidence", str(esc["by_reason"]["low_confidence"])],
        ["Customer Requested", str(esc["by_reason"]["customer_requested"])],
        ["Other", str(esc["by_reason"]["other"])],
        ["Resolved", str(esc["resolved_count"])],
        ["Pending", str(esc["pending_count"])],
        [
            "Avg Resolution Time",
            f"{esc['avg_resolution_time_hours']} hrs" if esc["avg_resolution_time_hours"] else "N/A",
        ],
    ]
    elements.append(_make_table(
        ["Metric", "Value"],
        esc_summary_rows,
        col_widths=[page_width * 0.55, page_width * 0.45],
    ))

    # ── Agent Performance ─────────────────────────────────
    if agents:
        elements.append(PageBreak())
        elements.append(Paragraph("Agent Performance", _SECTION_STYLE))
        agent_rows = []
        for a in agents:
            agent_rows.append([
                a["agent_name"],
                str(a["tickets_assigned"]),
                str(a["tickets_resolved"]),
                str(a["pending_tickets"]),
                f"{a['avg_resolution_time_hours']} hrs" if a["avg_resolution_time_hours"] else "N/A",
            ])
        cw = page_width / 5
        elements.append(_make_table(
            ["Agent", "Assigned", "Resolved", "Pending", "Avg Resolution"],
            agent_rows,
            col_widths=[cw] * 5,
        ))

    # ── Query Trends (table) ──────────────────────────────
    if trends:
        elements.append(Paragraph("Query Trends (Daily)", _SECTION_STYLE))
        trend_rows = []
        for t in trends[-30:]:  # last 30 days max
            trend_rows.append([
                t["date"],
                str(t["query_count"]),
                str(t["escalation_count"]),
            ])
        tw = page_width / 3
        elements.append(_make_table(
            ["Date", "Queries", "Escalations"],
            trend_rows,
            col_widths=[tw] * 3,
        ))

    # ── Top Queries ───────────────────────────────────────
    if top_q:
        elements.append(Paragraph("Top Queries", _SECTION_STYLE))
        tq_rows = []
        for q in top_q:
            text = q["query_text"][:80] + ("…" if len(q["query_text"]) > 80 else "")
            tq_rows.append([
                text,
                str(q["count"]),
                f"{round(q['avg_confidence'] * 100, 1)}%",
            ])
        elements.append(_make_table(
            ["Query", "Count", "Avg Confidence"],
            tq_rows,
            col_widths=[page_width * 0.6, page_width * 0.15, page_width * 0.25],
        ))

    doc.build(elements)
    return buf.getvalue()


def generate_escalation_pdf(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> bytes:
    """Generate an escalation-focused PDF report."""
    q = db.query(Ticket).order_by(Ticket.created_at.desc())
    q = _date_filter(q, Ticket.created_at, start_date, end_date)
    tickets = q.all()

    esc = analytics_service.get_escalation_metrics(db, start_date, end_date)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=30 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    elements = []
    page_width = A4[0] - 40 * mm

    elements.append(Spacer(1, 40))
    elements.append(Paragraph("SupportIQ Escalation Report", _TITLE_STYLE))

    date_range_str = "All Time"
    if start_date and end_date:
        date_range_str = f"{start_date.strftime('%d %b %Y')} — {end_date.strftime('%d %b %Y')}"
    elif start_date:
        date_range_str = f"From {start_date.strftime('%d %b %Y')}"
    elif end_date:
        date_range_str = f"Until {end_date.strftime('%d %b %Y')}"

    elements.append(Paragraph(
        f"Period: {date_range_str}<br/>Generated: {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}",
        _SUBTITLE_STYLE,
    ))

    # Summary
    elements.append(Paragraph("Summary", _SECTION_STYLE))
    summary_rows = [
        ["Total Escalations", str(esc["total_escalations"])],
        ["Escalation Rate", f"{esc['escalation_rate']}%"],
        ["Resolved", str(esc["resolved_count"])],
        ["Pending", str(esc["pending_count"])],
        [
            "Avg Resolution Time",
            f"{esc['avg_resolution_time_hours']} hrs" if esc["avg_resolution_time_hours"] else "N/A",
        ],
    ]
    elements.append(_make_table(
        ["Metric", "Value"],
        summary_rows,
        col_widths=[page_width * 0.55, page_width * 0.45],
    ))

    # Ticket details table
    if tickets:
        elements.append(Paragraph("Ticket Details", _SECTION_STYLE))
        ticket_rows = []
        for t in tickets:
            res_time = ""
            if t.resolved_at and t.created_at:
                delta = (t.resolved_at - t.created_at).total_seconds() / 3600
                res_time = f"{round(delta, 1)} hrs"

            ticket_rows.append([
                str(t.id),
                t.status.value,
                t.priority.value,
                (t.reason or "")[:40],
                t.created_at.strftime("%Y-%m-%d") if t.created_at else "",
                res_time or "—",
            ])

        cw = page_width / 6
        elements.append(_make_table(
            ["ID", "Status", "Priority", "Reason", "Created", "Resolution"],
            ticket_rows,
            col_widths=[cw * 0.6, cw * 0.9, cw * 0.8, cw * 1.6, cw * 1.0, cw * 1.1],
        ))

    doc.build(elements)
    return buf.getvalue()
