"""CSV export helper for list-returning reports."""
import csv
import io
import json

from django.http import HttpResponse


def dicts_to_csv(rows: list[dict], filename: str) -> HttpResponse:
    """Serialize report rows as a CSV attachment, JSON-encoding nested values."""
    output = io.StringIO(newline="")
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    if fieldnames:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                for key, value in row.items()
            })
    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
