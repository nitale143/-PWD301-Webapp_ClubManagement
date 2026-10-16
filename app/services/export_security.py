"""Treat user-controlled workbook values as text, never executable formulas."""


def safe_excel_text(value):
    """Chống chèn công thức Excel (CSV/Formula injection): thêm dấu ' trước ô bắt đầu bằng = + - @."""
    if not isinstance(value, str):
        return value
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


def safe_excel_row(values):
    """Áp safe_excel_text cho cả một dòng."""
    return [safe_excel_text(value) for value in values]
