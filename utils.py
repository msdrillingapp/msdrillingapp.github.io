from datetime import datetime
import pandas as pd
import pickle
import gzip
from typing import Any


def safe_timestamp_parse(timestamp_str):
    """Safely parse various timestamp formats including '03-Oct-2025'"""
    if timestamp_str is None:
        return None
    if isinstance(timestamp_str, datetime):
        return timestamp_str

    # Common timestamp formats to try (in order of likelihood)
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 2025-07-15 16:26:00
        '%Y-%m-%d %H:%M:%S.%f',  # 2025-07-15 16:26:00.123
        '%d-%b-%Y %H:%M:%S',  # 03-Oct-2025 16:26:00
        '%d-%b-%Y',  # 03-Oct-2025
        '%d.%m.%Y %H:%M:%S',  # 15.07.2025 16:26:00
        '%Y/%m/%d %H:%M:%S',  # 2025/07/15 16:26:00
        '%m/%d/%Y %H:%M:%S',  # 07/15/2025 16:26:00
        '%d %b %Y %H:%M:%S',  # 03 Oct 2025 16:26:00
        '%d %B %Y %H:%M:%S',  # 03 October 2025 16:26:00
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    print(f"Warning: Could not parse timestamp: {timestamp_str}")
    return None


def get_shape_marker(pile_code,pile_status):
    if pile_code.lower() == "Production Pile".lower():  # Circle
        shape='donut'
        # shape = 'circle'
    elif pile_code.lower() == "TEST PILE".lower():  # Square
        shape = 'square'
    elif pile_code.lower() == "REACTION PILE".lower():  # Octagon
        shape = 'target'
        # shape='diamond'
    else:
        shape ='triangle'
    if pile_status == 'Complete':
        shape += '_fill'
    # if pile_status !='Complete':
    #     shape+='-stroked'
    return shape


def is_timedelta_column(column):
    """Check if a pandas column is timedelta format"""
    return pd.api.types.is_timedelta64_dtype(column)


def seconds_to_smart_d_hms(seconds):
    """Convert seconds, only show days when > 0"""
    if pd.isna(seconds):
        return '00:00:00'

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    if days > 0:
        return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"



def pack(obj: Any) -> bytes:
    return gzip.compress(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))

def unpack(b: bytes) -> Any:
    return pickle.loads(gzip.decompress(b))