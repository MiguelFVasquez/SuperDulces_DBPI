import csv

def parse_csv(file_path: str) -> list[dict]:
    rows = []

    with open(file_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cleaned_row = {
                k.strip(): v.strip() if isinstance(v, str) else v
                for k, v in row.items()
                if k is not None
            }

            rows.append(cleaned_row)

    return rows