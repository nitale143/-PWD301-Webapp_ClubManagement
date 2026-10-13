"""Treat user-controlled workbook values as text, never executable formulas."""


def safe_excel_text(value):
    if not isinstance(value, str):
        return value
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


def safe_excel_row(values):
    return [safe_excel_text(value) for value in values]
