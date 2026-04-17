import pandas as pd


def export_clean_lang_files(file_path):
    # Load the Excel file
    df = pd.read_excel(file_path)

    # 1. THE NAN KILLER: Fill all empty cells with a blank string immediately
    df = df.fillna("")

    # The 'string' column (Column A) is our key
    key_col = df.columns[0]
    languages = df.columns[1:]

    for lang in languages:
        # Save filename as the language name (e.g., english.csv)
        filename = f"{lang.strip().lower()}.csv"

        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            for _, row in df.iterrows():
                key = str(row[key_col]).strip()
                value = str(row[lang]).strip()

                # Logic: If key starts with ##, write only the value (metadata)
                if key.startswith("##"):
                    f.write(f"{value}\n")

                # Logic: If both key and value are empty, just write a blank line
                elif not key and not value:
                    f.write("\n")

                # Logic: Standard key,value pair
                else:
                    f.write(f"""{key},"{value.replace('\"', '\'')}"\n""")

        print(f"Generated: {filename}")


# Run the export
export_clean_lang_files('lang.xlsx')
