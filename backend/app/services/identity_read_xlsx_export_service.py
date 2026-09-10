"""Human-readable XLSX representation of authority-selected System Groups."""

from __future__ import annotations

from datetime import date, datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from app.db.models import DuplicateScan
from app.identity_read.key_codec import serialize_versioned_identity_group_key
from app.services.identity_group_review_service import (
    VersionedIdentityGroupReviewService,
)
from app.services.identity_group_presentation import (
    human_review_presentation,
    system_evidence_tier,
)
from app.services.identity_read_export_service import (
    authority_selected_system_group_rows,
)


WORKBOOK_NOTICE = (
    "System-generated groups are suggestions requiring human review. "
    "They are not automatic merge instructions."
)

GROUP_COLUMNS = (
    "Candidate Group ID",
    "Canonical Group ID",
    "Review State",
    "System Evidence Tier",
    "Member Count",
    "Sites",
    "Primary Reason",
    "Human Decision",
    "Human Comment",
)

MEMBER_COLUMNS = (
    "Part No",
    "Description",
    "Site",
    "Inventory UOM",
    "Part Type",
    "Commodity Group 01",
    "Commodity Group 02",
    "Safety Code",
    "Accounting Group",
    "Product Code",
    "Product Family",
    "Product Category",
    "HSN/SAC Code",
    "Source Row / Stable Record Reference",
)

ALL_COLUMNS = GROUP_COLUMNS + MEMBER_COLUMNS

_MEMBER_FIELD_BY_COLUMN = {
    "Part No": "part_no",
    "Description": "description",
    "Site": "site_or_contract",
    "Inventory UOM": "uom",
    "Part Type": "part_type",
    "Commodity Group 01": "commodity_group_01",
    "Commodity Group 02": "commodity_group_02",
    "Safety Code": "safety_code",
    "Accounting Group": "accounting_group",
    "Product Code": "product_code",
    "Product Family": "product_family",
    "Product Category": "product_category",
    "HSN/SAC Code": "hsn_sac",
}

_REASONS = {
    "LIKELY_DUPLICATE_GROUP": (
        "Stronger deterministic evidence caused the system to suggest this group "
        "for human review."
    ),
    "POSSIBLE_DUPLICATE_GROUP_REVIEW": (
        "Deterministic review evidence caused the system to suggest this group; "
        "human review is required."
    ),
    "CONFLICT": (
        "Conflicting identity evidence prevents safe grouping; human review is required."
    ),
    "DEFERRED": (
        "Identity evaluation is incomplete or deferred; no same-identity conclusion is implied."
    ),
}

_HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
_HEADER_FONT = Font(color="FFFFFF", bold=True)
_GROUP_FILL = PatternFill("solid", fgColor="D9EAF7")
_THIN_GRAY = Side(style="thin", color="B7C9D6")
_BORDER = Border(left=_THIN_GRAY, right=_THIN_GRAY, top=_THIN_GRAY, bottom=_THIN_GRAY)


def write_spreadsheet_safe_cell(cell, value) -> None:
    """Write business-controlled text literally, never as an Excel formula."""
    if value is None:
        cell.value = ""
        return
    if isinstance(value, (datetime, date)):
        value = value.isoformat()
    cell.value = value
    if isinstance(value, str):
        cell.data_type = "s"


def reason_for_group_status(status: str) -> str:
    return _REASONS.get(
        status,
        "System-generated same-identity candidate requiring human review.",
    )


def _source_reference(row: dict) -> str:
    stable = str(row.get("stable_record_reference") or "")
    source = row.get("source_row_reference")
    return stable if source in (None, "") else f"Row {source} / {stable}"


def _group_values(label: str, group, state: dict | None, member_rows) -> tuple:
    status = group.status.value
    review_state, human_decision = human_review_presentation(state)
    sites = sorted({
        str(row.get("site_or_contract") or "").strip()
        for row in member_rows
        if str(row.get("site_or_contract") or "").strip()
    })
    return (
        label,
        serialize_versioned_identity_group_key(group.versioned_group_key),
        review_state,
        system_evidence_tier(status),
        group.member_count,
        ", ".join(sites) or "Not provided",
        reason_for_group_status(status),
        human_decision,
        (state or {}).get("comment") or "",
    )


def _member_values(row: dict) -> tuple:
    values = [row.get(_MEMBER_FIELD_BY_COLUMN[column]) for column in MEMBER_COLUMNS[:-1]]
    values.append(_source_reference(row))
    return tuple(values)


def _write_row(sheet, row_number: int, values) -> None:
    for column_number, value in enumerate(values, start=1):
        cell = sheet.cell(row=row_number, column=column_number)
        write_spreadsheet_safe_cell(cell, value)
        cell.border = _BORDER
        cell.alignment = Alignment(
            vertical="top", wrap_text=column_number in (4, 7, 8, 9)
        )


def _write_header(sheet, columns=ALL_COLUMNS) -> None:
    _write_row(sheet, 1, columns)
    for cell in sheet[1]:
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    sheet.freeze_panes = "A2"
    sheet.row_dimensions[1].height = 32


def _style_dimensions(sheet) -> None:
    widths = (20, 34, 36, 22, 14, 24, 54, 38, 42, 20, 48, 18, 16, 20, 22, 22, 18, 20, 20, 20, 20, 18, 48)
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width


def _write_summary(workbook, scan, snapshot, review_states) -> None:
    sheet = workbook.active
    sheet.title = "Summary"
    rows = (
        ("Inventory Identity Review Candidate Report", ""),
        ("Purpose", "Inventory identity review candidate report"),
        ("Important", WORKBOOK_NOTICE),
        ("Human authority", "Confirmed, rejected, or deferred human decisions override the system suggestion."),
        ("Workflow", "System suggests -> Human reviews -> Human decision becomes authoritative"),
        ("Report authority", "Advisory system suggestions with explicit human-review state"),
        ("Scan identifier", snapshot.scan_id),
        ("Scan name", scan.scan_name),
        ("Scan status", scan.status),
        ("Input record count", snapshot.canonical_record_count),
        ("System-Suggested Candidate Groups", snapshot.group_count),
        ("Human Confirmed Groups", sum(
            state.get("current_decision_type") in {
                "CONFIRM_ALL_AS_ONE", "CONFIRM_SELECTED", "SPLIT_PARTITIONS"
            } for state in review_states.values()
        )),
        ("Human Rejected Candidates", sum(
            state.get("current_decision_type") == "KEEP_ALL_SEPARATE"
            for state in review_states.values()
        )),
        ("Review Deferred / Unreviewed", sum(
            not state.get("reviewed") or state.get("current_decision_type") == "UNSURE"
            for state in review_states.values()
        )),
        ("Stronger Evidence candidates", snapshot.likely_group_count),
        ("Review Evidence candidates", snapshot.review_group_count),
        ("Conflict count", snapshot.conflict_count),
        ("Deferred count", snapshot.deferred_count),
        ("Unassigned count", snapshot.unassigned_count),
        ("Projection contract", snapshot.projection_contract.value),
        ("Source projection run", snapshot.source_projection_run_id),
    )
    for row_number, values in enumerate(rows, start=1):
        _write_row(sheet, row_number, values)
    sheet["A1"].font = Font(bold=True, size=16, color="1F4E78")
    for row_number in range(2, len(rows) + 1):
        sheet.cell(row_number, 1).font = Font(bold=True)
    for row_number in (2, 3, 4, 5, 6):
        sheet.cell(row_number, 2).alignment = Alignment(wrap_text=True, vertical="top")
    sheet.column_dimensions["A"].width = 28
    sheet.column_dimensions["B"].width = 100
    sheet.freeze_panes = "A2"


def authority_selected_system_groups_to_xlsx(db, scan_id: int) -> bytes:
    """Create an in-memory workbook from the exact System Group export projection."""
    snapshot, export_rows = authority_selected_system_group_rows(db, scan_id)
    scan = db.get(DuplicateScan, scan_id)
    review_states = VersionedIdentityGroupReviewService(db).current_states_for_snapshot(
        snapshot
    )
    rows_by_group = {}
    for row in export_rows:
        rows_by_group.setdefault(row["group_key"], []).append(row)

    workbook = Workbook()
    _write_summary(workbook, scan, snapshot, review_states)
    grouped = workbook.create_sheet("Candidate Groups")
    flat = workbook.create_sheet("Group Data")
    _write_header(grouped, GROUP_COLUMNS)
    _write_header(flat)

    grouped_row = 2
    flat_row = 2
    for group_index, group in enumerate(snapshot.groups, start=1):
        canonical_id = serialize_versioned_identity_group_key(group.versioned_group_key)
        label = f"CG-{group_index:06d}"
        member_rows = rows_by_group.get(canonical_id, ())
        group_values = _group_values(
            label, group, review_states.get(canonical_id), member_rows
        )
        _write_row(grouped, grouped_row, group_values)
        for column in range(1, len(GROUP_COLUMNS) + 1):
            grouped.cell(grouped_row, column).fill = _GROUP_FILL
        grouped_row += 1
        for member_row in member_rows:
            _write_row(flat, flat_row, group_values + _member_values(member_row))
            flat_row += 1

    for sheet in (grouped, flat):
        _style_dimensions(sheet)
    grouped.auto_filter.ref = f"A1:{get_column_letter(len(GROUP_COLUMNS))}{max(1, grouped.max_row)}"
    if flat.max_row >= 2:
        table = Table(
            displayName="SystemGroupData",
            ref=f"A1:{get_column_letter(len(ALL_COLUMNS))}{flat.max_row}",
        )
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False,
            showRowStripes=True, showColumnStripes=False,
        )
        flat.add_table(table)

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
