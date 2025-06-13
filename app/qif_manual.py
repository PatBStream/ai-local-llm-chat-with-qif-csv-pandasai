# app/qif_manual.py
import pandas as pd
from datetime import datetime
from typing import IO

def parse_qif(file_obj: IO[str]) -> pd.DataFrame:
    """
    Parse a QIF file-like object into a pandas DataFrame.
    Supports standard !Type: headers, date parsing, amounts, and key fields.
    """
    records = []
    record = {}

    for raw in file_obj:
        line = raw.strip()
        if not line or line.startswith('!'):
            continue

        key, val = line[0], line[1:].strip()

        # End of transaction
        if key == '^':
            if record:
                records.append(record)
                record = {}
            continue

        # Field mapping
        if key == 'D':
            # Dates like MM/DD/YYYY or MM/DD'YYYY
            norm = val.replace("'", "/")
            try:
                dt = datetime.strptime(norm, "%m/%d/%Y").date().isoformat()
                record['Date'] = dt
            except ValueError:
                record['Date'] = val
        elif key == 'T':
            # Amount; handle commas and parentheses
            cleaned = val.replace(',', '').replace('(', '-').replace(')', '')
            try:
                record['Amount'] = float(cleaned)
            except ValueError:
                record['Amount'] = val
        elif key == 'U':
            cleaned = val.replace(',', '').replace('(', '-').replace(')', '')
            try:
                record['OriginalAmount'] = float(cleaned)
            except ValueError:
                record['OriginalAmount'] = val
        elif key == 'P':
            record['Payee'] = val
        elif key == 'M':
            record['Memo'] = val
        elif key == 'L':
            record['Category'] = val
        elif key == 'N':
            record['Num'] = val
        elif key == 'C':
            record['Cleared'] = val
        elif key == 'A':
            # Address lines may span multiple; concatenate
            record.setdefault('Address', '')
            record['Address'] += val + ' '
        # extend with other QIF codes as needed…

    # Append last record if missing terminator
    if record:
        records.append(record)

    return pd.DataFrame.from_records(records)
