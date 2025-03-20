import re
from datetime import datetime
from tablemusthave import Table


def fix_date_collected(t: Table, colname: str, pattern: str):
    formats = [
        "%Y-%m-%d",  # 2024-02-24 (ISO format)
        "%d-%m-%Y",  # 24-02-2024
        "%m/%d/%Y",  # 02/24/2024 (US format)
        "%m/%d/%y",
        "%B %d, %Y",  # February 24, 2024
        "%b %d, %Y",  # Feb 24, 2024
        "%d %B %Y",  # 24 February 2024
        "%A, %d %B %Y",  # Saturday, 24 February 2024
        "%a %d %b %Y",  # Sat 24 Feb 2024
        "%Y-%j",  # 2024-055 (Year + Julian day)
        "%Y/%m/%d",  # 2024/02/24
        "%d/%m/%Y",  # 24/02/2024
        "%Y %U",  # 2024 08 (Year + Week number, Sunday start)
        "%Y %W",  # 2024 08 (Year + Week number, Monday start)
    ]

    def convert_date(date_string: str) -> str:
        if not date_string:
            return date_string
        for fmt in formats:
            print("Trying ", fmt)
            try:
                return datetime.strptime(date_string, fmt).strftime("%m-%d-%y")
            except ValueError:
                pass
        return date_string

    t.data[colname] = [convert_date(v) for v in t.get(colname)]


def fix_time_collected(t: Table, colname: str, pattern: str):
    formats = [
        "%H:%M:%S",  # 24-hour format (HH:MM:SS)
        "%I:%M:%S %p",  # 12-hour format with AM/PM (HH:MM:SS AM/PM)
        "%H:%M",  # 24-hour format (HH:MM)
        "%I:%M %p",  # 12-hour format with AM/PM (HH:MM AM/PM)
        "%H:%M:%S.%f",  # 24-hour format with microseconds (HH:MM:SS.ssssss)
        "%I:%M:%S.%f %p",  # 12-hour format with microseconds (HH:MM:SS.ssssss AM/PM)
    ]

    def convert_time(time_string: str) -> str:
        if not time_string:
            return time_string
        for fmt in formats:
            try:
                return datetime.strptime(time_string, fmt).strftime("%H:%M:%S")
            except ValueError:
                pass
        return time_string

    t.data[colname] = [convert_time(v) for v in t.get(colname)]


def fix_sample_start(t: Table, colname: str, pattern: str):
    print("FIXING")
    t.data[colname] = [f"S{v}" for v in t.get(colname)]


def fix_subject_start(t: Table, colname: str, pattern: str):
    t.data[colname] = [f"SB{v}" for v in t.get(colname)]


def fix_disallowed_sample_chars(t: Table, colname: str, pattern: str):
    raw_expression = re.sub(r"[\^\$\[\]\+]", "", pattern)
    t.data[colname] = [re.sub(f"[^{raw_expression}]", ".", v) for v in t.get(colname)]
