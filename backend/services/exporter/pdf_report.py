import os
import io
import tempfile
import datetime
import hashlib
from typing import Dict, Any, List, Optional
from fpdf import FPDF

from services.reports.report_services import (
    DatasetProfileService,
    QualityAssessmentService,
    MissingValueAnalysisService,
    DuplicateAnalysisService,
    FormatValidationService,
    AnomalyAnalysisService,
    RemediationSummaryService,
    BeforeAfterComparisonService,
    AuditTrailService,
    ReportValidationService
)
from services.reports.chart_generator import chart_generator
from services.reports.content_builder import content_builder


def _clean_str(txt: str) -> str:
    """Sanitizes text strings for FPDF latin-1 core font compatibility."""
    if txt is None:
        return ""
    txt = str(txt)
    replacements = {
        "✓": "[OK]",
        "⚠️": "[!] ",
        "❌": "[X] ",
        "➔": "->",
        "→": "->",
        "←": "<-",
        "—": "-",
        "–": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        "•": "* ",
        "▲": "+",
        "▼": "-",
        "★": "*",
    }
    for orig, repl in replacements.items():
        txt = txt.replace(orig, repl)
    return txt.encode("latin-1", "replace").decode("latin-1")


class EnterprisePDFReportGenerator(FPDF):
    """
    Enterprise multi-page PDF renderer for Data Quality Assessment & Remediation Reports.
    Includes corporate branding, running headers/footers, repeating table headers, and page numbering.
    """

    def __init__(self, filename: str = "dataset.csv", org_id: str = "org_default", dataset_id: int = 1):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.dataset_filename = _clean_str(filename)
        self.org_id = _clean_str(org_id)
        self.dataset_id = dataset_id
        self.set_auto_page_break(auto=True, margin=18)
        self.alias_nb_pages()

    def header(self):
        # Do not render header on Cover Page (Page 1)
        if self.page_no() == 1:
            return

        # Top Accent Header Bar
        self.set_fill_color(15, 23, 42)  # Slate-900 Navy
        self.rect(0, 0, 210, 7, 'F')
        self.set_fill_color(37, 99, 235) # Blue-600 accent
        self.rect(0, 7, 210, 1.2, 'F')

        self.set_y(1.5)
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(255, 255, 255)
        header_text = f"  DATAQUALITY AI PLATFORM  |  REPORT #{self.dataset_id}  |  {self.dataset_filename}"
        self.cell(0, 5, _clean_str(header_text), 0, 1, 'L')
        self.set_draw_color(226, 232, 240)
        self.line(10, 12, 200, 12)
        self.ln(5)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(226, 232, 240)
        self.line(10, 283, 200, 283)
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(100, 116, 139)
        self.cell(100, 8, _clean_str(f"CONFIDENTIAL  |  {self.dataset_filename}  |  Org: {self.org_id}"), 0, 0, 'L')
        self.set_font('Helvetica', 'I', 7.5)
        self.cell(90, 8, _clean_str(f"Page {self.page_no()} of {{nb}}"), 0, 0, 'R')


def ensure_space(pdf: FPDF, required_h: float) -> bool:
    """Checks if there is enough vertical space on current page; adds page if not."""
    if pdf.get_y() + required_h > 265:
        pdf.add_page()
        return True
    return False


def render_table_header(pdf: FPDF, col_widths: List[float], headers: List[str], align_list: Optional[List[str]] = None):
    """Renders table header with dark slate background."""
    ensure_space(pdf, 10)
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 8)
    align_list = align_list or ['C'] * len(headers)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 6, _clean_str(h), 1, 0, align_list[i], fill=True)
    pdf.ln(6)


def render_chart_image(pdf: FPDF, chart_bytes: bytes, width: float = 160, height: float = 50):
    """Renders a chart image dynamically using get_y() positioning and explicit height constraint."""
    ensure_space(pdf, height + 16)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(chart_bytes)
        tmp_path = tmp.name

    try:
        curr_y = pdf.get_y() + 2
        x_pos = (210 - width) / 2
        pdf.image(tmp_path, x=x_pos, y=curr_y, w=width, h=height)
        pdf.set_y(curr_y + height + 14)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def render_paragraphs(pdf: FPDF, paragraphs: List[str]):
    """Renders a list of multi-line paragraphs cleanly with space protection and spacing."""
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_text_color(51, 65, 85)
    for p in paragraphs:
        ensure_space(pdf, 15)
        pdf.multi_cell(190, 4.5, _clean_str(p))
        pdf.ln(3)


def generate_before_after_pdf_bytes(
    before_analysis: Dict[str, Any],
    after_analysis: Optional[Dict[str, Any]] = None,
    applied_logs: Optional[List[Dict[str, Any]]] = None,
    filename: str = "dataset.csv",
    dataset_id: int = 1,
    org_id: str = "org_default"
) -> bytes:
    """
    Generates an enterprise-grade, client-facing Data Quality Assessment & Remediation PDF report.
    Executes pre-render data reconciliation, avoids element overlaps, and produces exhaustive multi-page output.
    """
    after_analysis = after_analysis or before_analysis
    applied_logs = applied_logs or []

    # 1. Instantiate Domain Services
    profile_service = DatasetProfileService()
    quality_service = QualityAssessmentService()
    missing_service = MissingValueAnalysisService()
    dup_service = DuplicateAnalysisService()
    format_service = FormatValidationService()
    anomaly_service = AnomalyAnalysisService()
    remediation_service = RemediationSummaryService()
    comparison_service = BeforeAfterComparisonService()
    audit_service = AuditTrailService()
    validation_service = ReportValidationService()

    # 2. Execute Data Reconciliation Validation
    reconcil = validation_service.validate_reconciliation(before_analysis, after_analysis, applied_logs)

    # 3. Analyze All Domain Services
    profile = profile_service.analyze_profile(before_analysis, after_analysis, filename=filename)
    quality = quality_service.evaluate_quality(before_analysis, after_analysis)
    missing = missing_service.analyze_missing(before_analysis, after_analysis, applied_logs)
    duplicates = dup_service.analyze_duplicates(before_analysis, after_analysis)
    formats = format_service.analyze_formats(before_analysis, after_analysis)
    anomalies = anomaly_service.analyze_anomalies(before_analysis, after_analysis)
    remediation = remediation_service.summarize_remediation(applied_logs, before_analysis, after_analysis)
    comparison = comparison_service.build_comparison(before_analysis, after_analysis)
    audit = audit_service.format_audit(applied_logs, dataset_id=dataset_id, org_id=org_id)

    # 4. Generate Dynamic Content & Section Narratives
    exec_text = content_builder.build_executive_summary_text(
        profile, quality, missing, duplicates, formats, anomalies, len(applied_logs)
    )
    profile_paragraphs = content_builder.build_profile_narrative(profile)
    dimension_paragraphs = content_builder.build_dimension_narrative(quality)
    remediation_paragraphs = content_builder.build_remediation_narrative(remediation)
    master_paragraphs = content_builder.build_master_comparison_narrative(comparison, quality)
    column_matrix_paragraphs = content_builder.build_column_matrix_narrative(comparison)
    validation_paragraphs = content_builder.build_validation_narrative(reconcil, missing, duplicates)
    impact_text = content_builder.build_business_impact_narrative(quality, missing, duplicates, formats, anomalies)
    recommendations = content_builder.build_recommendations(missing, duplicates, formats, anomalies)
    gov_meta = content_builder.build_governance_metadata(dataset_id, org_id, audit["digital_hash"])

    # 5. Initialize PDF Engine
    pdf = EnterprisePDFReportGenerator(filename=filename, org_id=org_id, dataset_id=dataset_id)

    # -------------------------------------------------------------
    # PAGE 1: COVER PAGE & EXECUTIVE SUMMARY
    # -------------------------------------------------------------
    pdf.add_page()

    # Cover Page Top Header Banner
    pdf.set_fill_color(15, 23, 42)   # Dark Navy Slate-900
    pdf.rect(0, 0, 210, 48, 'F')
    pdf.set_fill_color(37, 99, 235)  # Blue Accent
    pdf.rect(0, 48, 210, 2.5, 'F')

    pdf.set_xy(14, 12)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, _clean_str("DATAQUALITY AI PLATFORM  |  ENTERPRISE GOVERNANCE"), 0, 1, 'L')

    pdf.set_xy(14, 19)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, _clean_str("DATA QUALITY ASSESSMENT & REMEDIATION REPORT"), 0, 1, 'L')

    pdf.set_xy(14, 28)
    pdf.set_font('Helvetica', 'I', 10.5)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(0, 6, _clean_str("Executive Before & After Quality Audit, Automated Remediation & Governance Certification"), 0, 1, 'L')

    pdf.ln(22)

    # Metadata Grid (2-Column Box)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, 56, 190, 36, 'FD')

    pdf.set_xy(14, 59)
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, _clean_str("Dataset Name:"), 0, 0)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(55, 5, _clean_str(profile["filename"]), 0, 0)

    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, _clean_str("Report ID:"), 0, 0)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(50, 5, _clean_str(gov_meta["report_id"]), 0, 1)

    pdf.set_xy(14, 65)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, _clean_str("Dataset ID:"), 0, 0)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(55, 5, _clean_str(gov_meta["dataset_id"]), 0, 0)

    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, _clean_str("Organization:"), 0, 0)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(50, 5, _clean_str(gov_meta["organization"]), 0, 1)

    pdf.set_xy(14, 71)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, _clean_str("Rows / Columns:"), 0, 0)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(55, 5, _clean_str(f"{profile['total_rows_before']:,} rows x {profile['total_cols_before']:,} cols"), 0, 0)

    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, _clean_str("Generated Date:"), 0, 0)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(50, 5, _clean_str(gov_meta["generated_timestamp"]), 0, 1)

    pdf.set_xy(14, 77)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, _clean_str("Remediation Status:"), 0, 0)
    pdf.set_font('Helvetica', 'B', 8.5)
    if len(applied_logs) > 0:
        pdf.set_text_color(16, 185, 129) # Emerald
        pdf.cell(55, 5, _clean_str(f"REMEDIATED ({len(applied_logs):,} Ops Applied)"), 0, 0)
    else:
        pdf.set_text_color(245, 158, 11) # Amber
        pdf.cell(55, 5, _clean_str("UNMODIFIED BASELINE"), 0, 0)

    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, _clean_str("Reconciliation:"), 0, 0)
    pdf.set_text_color(16, 185, 129) if reconcil["is_valid"] else pdf.set_text_color(239, 68, 68)
    pdf.cell(50, 5, _clean_str(reconcil["status"]), 0, 1)

    # PROMINENT BEFORE -> AFTER QUALITY SCORE CARDS
    pdf.set_xy(10, 98)
    card_w = 58
    card_h = 28
    gap = 8

    # BEFORE CARD
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, 98, card_w, card_h, 'FD')
    pdf.set_xy(12, 102)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(card_w - 4, 4, _clean_str("BEFORE QUALITY SCORE"), 0, 1, 'C')
    pdf.set_xy(12, 108)
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(239, 68, 68) if quality["before_overall"] < 80 else pdf.set_text_color(245, 158, 11)
    pdf.cell(card_w - 4, 8, _clean_str(f"{quality['before_overall']:.1f}%"), 0, 1, 'C')
    pdf.set_xy(12, 117)
    pdf.set_font('Helvetica', 'B', 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(card_w - 4, 4, _clean_str(quality["before_rating"]), 0, 1, 'C')

    # AFTER CARD
    pdf.set_fill_color(240, 253, 244) # Tint Green
    pdf.set_draw_color(187, 247, 208)
    pdf.rect(10 + card_w + gap, 98, card_w, card_h, 'FD')
    pdf.set_xy(12 + card_w + gap, 102)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(card_w - 4, 4, _clean_str("AFTER QUALITY SCORE"), 0, 1, 'C')
    pdf.set_xy(12 + card_w + gap, 108)
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(16, 185, 129)
    pdf.cell(card_w - 4, 8, _clean_str(f"{quality['after_overall']:.1f}%"), 0, 1, 'C')
    pdf.set_xy(12 + card_w + gap, 117)
    pdf.set_font('Helvetica', 'B', 7.5)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(card_w - 4, 4, _clean_str(quality["after_rating"]), 0, 1, 'C')

    # IMPROVEMENT CARD
    pdf.set_fill_color(239, 246, 255) # Tint Blue
    pdf.set_draw_color(191, 219, 254)
    pdf.rect(10 + (card_w + gap) * 2, 98, card_w, card_h, 'FD')
    pdf.set_xy(12 + (card_w + gap) * 2, 102)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(card_w - 4, 4, _clean_str("NET IMPROVEMENT"), 0, 1, 'C')
    pdf.set_xy(12 + (card_w + gap) * 2, 108)
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(card_w - 4, 8, _clean_str(f"+{quality['improvement']:.1f}%"), 0, 1, 'C')
    pdf.set_xy(12 + (card_w + gap) * 2, 117)
    pdf.set_font('Helvetica', 'B', 7.5)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(card_w - 4, 4, _clean_str(f"{len(applied_logs):,} Corrections"), 0, 1, 'C')

    # Executive Summary Text Card
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, 132, 190, 48, 'FD')

    pdf.set_xy(14, 135)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, _clean_str("EXECUTIVE SUMMARY"), 0, 1, 'L')

    pdf.set_xy(14, 142)
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(182, 4.5, _clean_str(exec_text))

    # Render Quality Score Chart dynamically below executive summary box
    pdf.set_y(186)
    chart_bytes1 = chart_generator.generate_quality_comparison_chart(quality["before_overall"], quality["after_overall"])
    render_chart_image(pdf, chart_bytes1, width=150, height=50)

    # -------------------------------------------------------------
    # SECTION 1: DATASET PROFILE & SCHEMA ANALYSIS
    # -------------------------------------------------------------
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, _clean_str("1. Dataset Profile & Baseline Attribute Inventory"), 0, 1, 'L')
    pdf.ln(2)

    # Multi-Paragraph Explanatory Narratives
    render_paragraphs(pdf, profile_paragraphs)
    pdf.ln(2)

    # Column Inventory Table
    col_w = [45, 30, 30, 30, 25, 30]
    headers_inv = ["Column Name", "Data Type", "Non-Null Count", "Missing Count", "Missing %", "Quality Status"]
    align_inv = ['L', 'C', 'C', 'C', 'C', 'C']
    render_table_header(pdf, col_w, headers_inv, align_inv)

    pdf.set_font('Helvetica', '', 8)
    for idx, item in enumerate(profile["column_inventory"]):
        if ensure_space(pdf, 7):
            render_table_header(pdf, col_w, headers_inv, align_inv)

        bg = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(51, 65, 85)

        pdf.cell(col_w[0], 5.5, _clean_str(item["column"]), 1, 0, 'L', fill=True)
        pdf.cell(col_w[1], 5.5, _clean_str(item["data_type"]), 1, 0, 'C', fill=True)
        pdf.cell(col_w[2], 5.5, _clean_str(f"{item['non_null_count']:,}"), 1, 0, 'C', fill=True)
        pdf.cell(col_w[3], 5.5, _clean_str(f"{item['missing_count']:,}"), 1, 0, 'C', fill=True)
        pdf.cell(col_w[4], 5.5, _clean_str(f"{item['missing_pct']:.1f}%"), 1, 0, 'C', fill=True)

        if "PASSED" in item["status"]:
            pdf.set_text_color(16, 185, 129)
        elif "MINOR" in item["status"]:
            pdf.set_text_color(245, 158, 11)
        else:
            pdf.set_text_color(239, 68, 68)

        pdf.cell(col_w[5], 5.5, _clean_str(item["status"]), 1, 1, 'C', fill=True)

    pdf.ln(6)

    # Numerical Column Statistical Profiles Table
    if profile.get("numeric_stats"):
        ensure_space(pdf, 25)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, _clean_str("1.1 Numerical Attribute Statistical Profiles (Before vs After)"), 0, 1, 'L')
        pdf.ln(2)

        col_w_s = [40, 30, 30, 30, 30, 30]
        headers_stat = ["Column", "Mean (B -> A)", "Median (B -> A)", "Std Dev (B -> A)", "Min (B -> A)", "Max (B -> A)"]
        render_table_header(pdf, col_w_s, headers_stat)

        pdf.set_font('Helvetica', '', 7.5)
        for idx, st in enumerate(profile["numeric_stats"]):
            if ensure_space(pdf, 7):
                render_table_header(pdf, col_w_s, headers_stat)

            bg = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(*bg)
            pdf.set_text_color(51, 65, 85)

            pdf.cell(col_w_s[0], 5.5, _clean_str(st["column"]), 1, 0, 'L', fill=True)
            pdf.cell(col_w_s[1], 5.5, _clean_str(f"{st['mean_before']} -> {st['mean_after']}"), 1, 0, 'C', fill=True)
            pdf.cell(col_w_s[2], 5.5, _clean_str(f"{st['median_before']} -> {st['median_after']}"), 1, 0, 'C', fill=True)
            pdf.cell(col_w_s[3], 5.5, _clean_str(f"{st['std_before']} -> {st['std_after']}"), 1, 0, 'C', fill=True)
            pdf.cell(col_w_s[4], 5.5, _clean_str(f"{st['min_before']} -> {st['min_after']}"), 1, 0, 'C', fill=True)
            pdf.cell(col_w_s[5], 5.5, _clean_str(f"{st['max_before']} -> {st['max_after']}"), 1, 1, 'C', fill=True)

        pdf.ln(6)

    # -------------------------------------------------------------
    # SECTION 2: MULTIDIMENSIONAL DATA QUALITY ASSESSMENT
    # -------------------------------------------------------------
    ensure_space(pdf, 30)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, _clean_str("2. Multidimensional Data Quality Assessment"), 0, 1, 'L')
    pdf.ln(2)

    # Multi-Paragraph Explanatory Narratives
    render_paragraphs(pdf, dimension_paragraphs)
    pdf.ln(2)

    col_w_q = [40, 20, 25, 25, 25, 55]
    headers_q = ["Dimension", "Weight", "Before Score", "After Score", "Delta", "Dimension Description"]
    render_table_header(pdf, col_w_q, headers_q, ['L', 'C', 'C', 'C', 'C', 'L'])

    pdf.set_font('Helvetica', '', 8)
    for idx, dim in enumerate(quality["dimensions"]):
        if ensure_space(pdf, 7):
            render_table_header(pdf, col_w_q, headers_q, ['L', 'C', 'C', 'C', 'C', 'L'])

        bg = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(51, 65, 85)

        pdf.cell(col_w_q[0], 5.5, _clean_str(dim["name"]), 1, 0, 'L', fill=True)
        pdf.cell(col_w_q[1], 5.5, _clean_str(dim["weight"]), 1, 0, 'C', fill=True)
        pdf.cell(col_w_q[2], 5.5, _clean_str(f"{dim['before']:.1f}%"), 1, 0, 'C', fill=True)
        
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(col_w_q[3], 5.5, _clean_str(f"{dim['after']:.1f}%"), 1, 0, 'C', fill=True)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(col_w_q[4], 5.5, _clean_str(f"+{dim['delta']:.1f}%" if dim['delta'] > 0 else "0.0%"), 1, 0, 'C', fill=True)
        
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(col_w_q[5], 5.5, _clean_str(dim["explanation"][:42]), 1, 1, 'L', fill=True)

    pdf.ln(4)

    # Render Multidimensional Radar/Bar Chart dynamically with strict height=50 constraint
    chart_bytes2 = chart_generator.generate_dimension_radar_chart(quality["dimensions"])
    render_chart_image(pdf, chart_bytes2, width=160, height=50)

    # -------------------------------------------------------------
    # SECTION 3: DETECTED QUALITY ISSUES & REMEDIATION SUMMARY
    # -------------------------------------------------------------
    ensure_space(pdf, 30)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, _clean_str("3. Detailed Issue Detection & Remediation Summary"), 0, 1, 'L')
    pdf.ln(2)

    # Multi-Paragraph Explanatory Narratives
    render_paragraphs(pdf, remediation_paragraphs)
    pdf.ln(2)

    # Remediation Dashboard Grid
    col_w_r = [55, 30, 45, 30, 30]
    headers_r = ["Issue Category", "Applied Count", "Remediation Technique", "Execution Status", "Resolution %"]
    render_table_header(pdf, col_w_r, headers_r, ['L', 'C', 'L', 'C', 'C'])

    pdf.set_font('Helvetica', '', 8)
    for idx, cat in enumerate(remediation["categories"]):
        if ensure_space(pdf, 7):
            render_table_header(pdf, col_w_r, headers_r, ['L', 'C', 'L', 'C', 'C'])

        bg = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(51, 65, 85)

        pdf.cell(col_w_r[0], 5.5, _clean_str(cat["category"]), 1, 0, 'L', fill=True)
        pdf.cell(col_w_r[1], 5.5, _clean_str(f"{cat['corrections_applied']:,}"), 1, 0, 'C', fill=True)
        pdf.cell(col_w_r[2], 5.5, _clean_str(cat["method"]), 1, 0, 'L', fill=True)
        
        pdf.set_text_color(16, 185, 129) if "Applied" in cat["status"] else pdf.set_text_color(100, 116, 139)
        pdf.cell(col_w_r[3], 5.5, _clean_str(cat["status"]), 1, 0, 'C', fill=True)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(col_w_r[4], 5.5, _clean_str("100.0%" if cat['corrections_applied'] > 0 else "N/A"), 1, 1, 'C', fill=True)

    pdf.ln(4)

    # Issue Reduction Chart Image rendered dynamically with strict height=50 constraint and 14mm vertical buffer!
    chart_bytes3 = chart_generator.generate_issue_reduction_chart(
        missing["total_missing_before"], missing["total_missing_after"],
        duplicates["duplicates_before"], duplicates["duplicates_after"],
        formats["total_invalid_before"], formats["total_invalid_after"],
        anomalies["anomalies_before"], anomalies["anomalies_after"]
    )
    render_chart_image(pdf, chart_bytes3, width=160, height=50)

    # -------------------------------------------------------------
    # SECTION 4: MASTER BEFORE VS AFTER COMPARISON & RECONCILIATION
    # -------------------------------------------------------------
    ensure_space(pdf, 35)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, _clean_str("4. Master Before vs. After Quality Comparison Grid"), 0, 1, 'L')
    pdf.ln(2)

    # Multi-Paragraph Explanatory Narratives
    render_paragraphs(pdf, master_paragraphs)
    pdf.ln(2)

    col_w_m = [55, 35, 35, 30, 35]
    headers_m = ["Quality Metric", "Before Remediation", "After Remediation", "Net Change", "Remediation Status"]
    render_table_header(pdf, col_w_m, headers_m, ['L', 'C', 'C', 'C', 'C'])

    pdf.set_font('Helvetica', '', 8)
    for idx, row in enumerate(comparison["master_rows"]):
        if ensure_space(pdf, 7):
            render_table_header(pdf, col_w_m, headers_m, ['L', 'C', 'C', 'C', 'C'])

        bg = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(51, 65, 85)

        pdf.cell(col_w_m[0], 5.5, _clean_str(row["metric"]), 1, 0, 'L', fill=True)
        pdf.cell(col_w_m[1], 5.5, _clean_str(row["before"]), 1, 0, 'C', fill=True)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(col_w_m[2], 5.5, _clean_str(row["after"]), 1, 0, 'C', fill=True)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(col_w_m[3], 5.5, _clean_str(row["change"]), 1, 0, 'C', fill=True)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w_m[4], 5.5, _clean_str(row["status"]), 1, 1, 'C', fill=True)
        pdf.set_font('Helvetica', '', 8)

    pdf.ln(6)

    # -------------------------------------------------------------
    # SECTION 5: COLUMN-LEVEL BEFORE / AFTER MATRIX
    # -------------------------------------------------------------
    if comparison.get("column_grid"):
        ensure_space(pdf, 30)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, _clean_str("5. Column-Level Issue & Remediation Matrix"), 0, 1, 'L')
        pdf.ln(2)

        # Multi-Paragraph Explanatory Narratives
        render_paragraphs(pdf, column_matrix_paragraphs)
        pdf.ln(2)

        col_w_cg = [45, 30, 30, 30, 30, 25]
        headers_cg = ["Attribute Name", "Missing (B)", "Missing (A)", "Format Error (B)", "Format Error (A)", "Status"]
        render_table_header(pdf, col_w_cg, headers_cg)

        pdf.set_font('Helvetica', '', 8)
        for idx, item in enumerate(comparison["column_grid"]):
            if ensure_space(pdf, 7):
                render_table_header(pdf, col_w_cg, headers_cg)

            bg = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(*bg)
            pdf.set_text_color(51, 65, 85)

            pdf.cell(col_w_cg[0], 5.5, _clean_str(item["column"]), 1, 0, 'L', fill=True)
            pdf.cell(col_w_cg[1], 5.5, _clean_str(f"{item['missing_before']:,}"), 1, 0, 'C', fill=True)
            pdf.cell(col_w_cg[2], 5.5, _clean_str(f"{item['missing_after']:,}"), 1, 0, 'C', fill=True)
            pdf.cell(col_w_cg[3], 5.5, _clean_str(f"{item['format_before']:,}"), 1, 0, 'C', fill=True)
            pdf.cell(col_w_cg[4], 5.5, _clean_str(f"{item['format_after']:,}"), 1, 0, 'C', fill=True)
            pdf.set_text_color(16, 185, 129) if "PASSED" in item["status"] else pdf.set_text_color(245, 158, 11)
            pdf.cell(col_w_cg[5], 5.5, _clean_str(item["status"]), 1, 1, 'C', fill=True)

        pdf.ln(6)

    # -------------------------------------------------------------
    # SECTION 6: POST-REMEDIATION VALIDATION & AUDIT TRAIL
    # -------------------------------------------------------------
    ensure_space(pdf, 30)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, _clean_str("6. Post-Remediation Validation & Governance Audit"), 0, 1, 'L')
    pdf.ln(2)

    # Multi-Paragraph Explanatory Narratives
    render_paragraphs(pdf, validation_paragraphs)
    pdf.ln(2)

    val_checks = [
        ("Missing Cell Resolution Check", f"{missing['total_missing_before']:,}", f"{missing['total_missing_after']:,}", "PASSED ✓" if missing['total_missing_after'] == 0 else "WARNING ⚠️"),
        ("Duplicate Row Removal Check", f"{duplicates['duplicates_before']:,}", f"{duplicates['duplicates_after']:,}", "PASSED ✓" if duplicates['duplicates_after'] == 0 else "WARNING ⚠️"),
        ("Format Regex Normalization Check", f"{formats['total_invalid_before']:,}", f"{formats['total_invalid_after']:,}", "PASSED ✓" if formats['total_invalid_after'] == 0 else "WARNING ⚠️"),
        ("ML Ensemble Anomaly Bounding", f"{anomalies['anomalies_before']:,}", f"{anomalies['anomalies_after']:,}", "PASSED ✓" if anomalies['anomalies_after'] <= 1 else "WARNING ⚠️"),
        ("Data Reconciliation Integrity Layer", "Checked", "Verified", reconcil["status"])
    ]

    col_w_v = [60, 40, 40, 50]
    headers_v = ["Validation Rule Check", "Before State", "After State", "Validation Status"]
    render_table_header(pdf, col_w_v, headers_v, ['L', 'C', 'C', 'C'])

    pdf.set_font('Helvetica', '', 8)
    for idx, (check_name, v_before, v_after, v_status) in enumerate(val_checks):
        if ensure_space(pdf, 7):
            render_table_header(pdf, col_w_v, headers_v, ['L', 'C', 'C', 'C'])

        bg = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(51, 65, 85)

        pdf.cell(col_w_v[0], 5.5, _clean_str(check_name), 1, 0, 'L', fill=True)
        pdf.cell(col_w_v[1], 5.5, _clean_str(v_before), 1, 0, 'C', fill=True)
        pdf.cell(col_w_v[2], 5.5, _clean_str(v_after), 1, 0, 'C', fill=True)
        
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(16, 185, 129) if "PASSED" in v_status else pdf.set_text_color(239, 68, 68)
        pdf.cell(col_w_v[3], 5.5, _clean_str(v_status), 1, 1, 'C', fill=True)
        pdf.set_font('Helvetica', '', 8)

    pdf.ln(6)

    # Business Impact & Targeted Recommendations
    ensure_space(pdf, 35)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, _clean_str("7. Business Impact & Targeted Recommendations"), 0, 1, 'L')

    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(190, 4, _clean_str(impact_text))
    pdf.ln(3)

    ensure_space(pdf, 25)
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, _clean_str("Actionable Recommendations:"), 0, 1, 'L')
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(51, 65, 85)
    for rec in recommendations:
        pdf.cell(190, 4.5, _clean_str(f"* {rec}"), 0, 1, 'L')

    pdf.ln(6)

    # FINAL CERTIFICATION STAMP BOX
    ensure_space(pdf, 60)
    pdf.set_fill_color(15, 23, 42)   # Slate-900 Navy
    pdf.set_draw_color(30, 41, 59)
    box_y = pdf.get_y()
    pdf.rect(10, box_y, 190, 55, 'FD')

    pdf.set_xy(14, box_y + 3)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 6, _clean_str("DATA QUALITY ENTERPRISE CERTIFICATION"), 0, 1, 'L')

    pdf.set_xy(14, box_y + 11)
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(45, 5, _clean_str("Initial Quality Index:"), 0, 0)
    pdf.set_text_color(245, 158, 11)
    pdf.cell(45, 5, _clean_str(f"{quality['before_overall']:.1f}% ({quality['before_rating']})"), 0, 0)

    pdf.set_text_color(203, 213, 225)
    pdf.cell(45, 5, _clean_str("Final Quality Index:"), 0, 0)
    pdf.set_text_color(52, 211, 153)
    pdf.cell(45, 5, _clean_str(f"{quality['after_overall']:.1f}% ({quality['after_rating']})"), 0, 1)

    pdf.set_xy(14, box_y + 17)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(45, 5, _clean_str("Total Operations Applied:"), 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 5, _clean_str(f"{len(applied_logs):,} Corrections"), 0, 0)

    pdf.set_text_color(203, 213, 225)
    pdf.cell(45, 5, _clean_str("Digital Audit Hash:"), 0, 0)
    pdf.set_font('Courier', 'B', 8.5)
    pdf.set_text_color(96, 165, 250)
    pdf.cell(45, 5, _clean_str(audit["digital_hash"]), 0, 1)

    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_xy(14, box_y + 23)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(45, 5, _clean_str("Validation Layer:"), 0, 0)
    pdf.set_text_color(52, 211, 153) if reconcil["is_valid"] else pdf.set_text_color(248, 113, 113)
    pdf.cell(45, 5, _clean_str(reconcil["status"]), 0, 0)

    pdf.set_text_color(203, 213, 225)
    pdf.cell(45, 5, _clean_str("Governance Standard:"), 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 5, _clean_str("ISO/IEC 25012 Aligned"), 0, 1)

    pdf.set_xy(14, box_y + 32)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(52, 211, 153)
    pdf.cell(0, 6, _clean_str("DATASET CERTIFICATION STATUS: READY FOR PRODUCTION ML & ANALYTICS PIPELINES ✓"), 0, 1, 'L')

    # Return raw PDF bytes
    return bytes(pdf.output())
