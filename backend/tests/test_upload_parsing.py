import datetime
import io

import pandas as pd
from openpyxl import Workbook

from app.services.validation_service import _parse_upload_dataframe


def _workbook_bytes(rows):
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_xlsx_cells_read_as_the_previous_openpyxl_reader_did():
    content = _workbook_bytes([
        ["PART_NO", "DESCRIPTION", "CONTRACT", "UNIT_MEAS", "PRICE", "CREATED"],
        [332175, "Viola x will. Mix 6-Pack", 1010, "ST", 12.5, datetime.datetime(2024, 5, 1)],
        ["000123", "Leading zero text", "1003", "PCS", 1e-7, None],
        [1.5, "Aluminium bar (SPR-110) 70mm Bronze 10'", 9010, None, 12345678901234, None],
        [None, None, None, None, None, None],
    ])

    parsed = _parse_upload_dataframe("parts.xlsx", content)

    expected = pd.read_excel(io.BytesIO(content), dtype=str, engine="openpyxl")
    pd.testing.assert_frame_equal(parsed, expected)
    assert parsed["PART_NO"].tolist()[:3] == ["332175", "000123", "1.5"]
    assert parsed["CONTRACT"].tolist()[0] == "1010"
