import pdfplumber
import sqlite3
import os
import argparse
import re
import logging
from src.logging_config import setup_logging

class PDFTableExtractor:
    """
    Extracts table data from a specified range of pages in a PDF file.
    """

    def __init__(self, pdf_path):
        """
        Initializes the extractor with the path to the PDF file.

        Args:
            pdf_path (str): The full path to the PDF file.

        Raises:
            FileNotFoundError: If the PDF file does not exist at the given path.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The PDF file was not found at: {pdf_path}")
        self.pdf_path = pdf_path

    def extract_tables(self, start_page, end_page):
        """
        Extracts all tables from the specified page range.

        Args:
            start_page (int): The starting page number (1-based).
            end_page (int): The ending page number (1-based).

        Returns:
            list: A list of all extracted tables. Each table is a list of rows,
                  and each row is a list of cell strings.
        """
        all_tables_data = []
        logging.info(f"Opening PDF: {os.path.basename(self.pdf_path)}")
        with pdfplumber.open(self.pdf_path) as pdf:
            # Adjust for 0-based indexing used by pdfplumber
            start_idx = start_page - 1
            end_idx = end_page - 1

            if start_idx >= len(pdf.pages):
                logging.error(f"Error: Start page {start_page} is beyond the end of the document ({len(pdf.pages)} pages).")
                return []

            logging.info(f"Processing pages from {start_page} to {end_page}...")
            for i in range(start_idx, min(end_idx + 1, len(pdf.pages))):
                page = pdf.pages[i]
                tables = page.extract_tables()
                if tables:
                    logging.info(f"  - Found {len(tables)} table(s) on page {i + 1}.")
                    # Clean up the data by removing None and replacing newlines
                    for table in tables:
                        cleaned_table = []
                        for row in table:
                            cleaned_row = [str(cell).replace('\n', ' ') if cell is not None else "" for cell in row]
                            cleaned_table.append(cleaned_row)
                        all_tables_data.append(cleaned_table)
                else:
                    logging.warning(f"  - No tables found on page {i + 1}.")
        return all_tables_data


class DatabaseManager:
    """
    Manages the creation of and insertion into an SQLite database.
    """

    def __init__(self, db_path):
        """
        Initializes the manager with the path to the SQLite database.
        """
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        """Establishes the database connection."""
        self.conn = sqlite3.connect(self.db_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

    def _is_valid_table_name(self, name):
        """Validates that the table name is safe to use in a query."""
        # Table names should start with a letter or underscore,
        # and contain only letters, numbers, or underscores.
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name)

    def create_error_table(self, table_name):
        """
        Creates a table with the given name if it doesn't already exist.
        The table has a flexible number of columns to accommodate different table structures.

        Args:
            table_name (str): The name for the new table.
        """
        if not self._is_valid_table_name(table_name):
            raise ValueError(f"Invalid table name provided: {table_name}")

        cursor = self.conn.cursor()
        # Drop the table if it exists to start fresh each time
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        # A generic table structure that can hold most tables.
        # We assume a max of 10 columns for future flexibility.
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                col1 TEXT, col2 TEXT, col3 TEXT, col4 TEXT, col5 TEXT,
                col6 TEXT, col7 TEXT, col8 TEXT, col9 TEXT, col10 TEXT
            )
        """)
        self.conn.commit()
        logging.info(f"Database '{os.path.basename(self.db_path)}' is ready. Table '{table_name}' created.")

    def insert_table_data(self, table_name, tables):
        """
        Inserts data from extracted tables into the specified table.

        Args:
            table_name (str): The name of the table to insert data into.
            tables (list): A list of tables, where each table is a list of rows.
        """
        cursor = self.conn.cursor()
        total_rows_inserted = 0
        # The column names, matching the CREATE TABLE statement
        column_names = [f'col{i}' for i in range(1, 11)]
        insert_query = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(['?'] * 10)})"

        for table in tables:
            for row in table:
                # Pad the row with empty strings to match the 10-column schema
                padded_row = (row + [""] * 10)[:10]
                cursor.execute(insert_query, padded_row)
                total_rows_inserted += 1
        self.conn.commit()
        logging.info(f"Successfully inserted {total_rows_inserted} rows into the '{table_name}' table.")


class SEWErrorCodeExtractor:
    """
    Extracts robust SEW error codes from PDF tables, handling multi-row error codes, suberrors, and page/table headers.
    """
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def is_header_or_page_row(self, row):
        """
        Improved header/page row detection:
        - Skips rows where the first column is a digit and the rest are empty or header-like (page number header).
        - Skips rows where the first two columns are header keywords or the row is truly empty.
        - Skips rows where the first column is a digit and the row is very short (likely a page header).
        """
        header_keywords = ["Error", "Code", "Designation", "Response (P)", "Suberror", "Possible cause", "Measure"]
        page_header_keywords = ["MOVIPRO", "ADC error list", "Service", "Operating Instructions", "SEW EURODRIVE"]
        # Check if the row is empty or all cells are None/empty
        if not row or all(cell is None or str(cell).strip() == "" for cell in row):
            return True
        # Check if the first two columns are header keywords
        if (str(row[0]).strip() in header_keywords or str(row[1]).strip() in header_keywords):
            return True
        # Check if the row is a page header (contains page header keywords)
        for cell in row:
            cell_str = str(cell).strip() if cell else ""
            if any(h.lower() == cell_str.lower() for h in page_header_keywords):
                return True
        # Check for page number header: first column is a digit, rest are empty or header-like
        if str(row[0]).strip().isdigit():
            nonempty = [str(cell).strip() for cell in row[1:]]
            # If all other columns are empty or header keywords, skip
            if all(cell == "" or cell in header_keywords for cell in nonempty):
                return True
            # If row is very short (2 columns or less), likely a page header
            if len([cell for cell in row if cell and str(cell).strip() != ""]) <= 2:
                return True
        return False

    def strip_bullets(self, text):
        if not text:
            return ""
        # Remove bullet character (•) only once in the regex
        return re.sub(r"[•]", "", text).strip()

    def clean_text(self, text):
        """
        Clean up text by:
        - Joining lines where a word is split with a hyphen at the end of a line (e.g., 'com-\nmand' -> 'command').
        - Preserving all original formatting (bullets, dashes, numbers, paragraphs).
        - Stripping leading/trailing whitespace and normalizing spaces.
        """
        if not text:
            return ""
        # Join hyphenated line breaks (word split across lines)
        # This regex finds a word ending with a hyphen at the end of a line, followed by a newline and a word on the next line
        # It replaces 'com-\nmand' with 'command'
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        # Replace multiple spaces with a single space, preserve newlines
        text = re.sub(r'[ ]+', ' ', text)
        # Normalize newlines (remove trailing spaces on each line)
        lines = [line.rstrip() for line in text.splitlines()]
        return '\n'.join(lines).strip()

    def extract_sew_error_codes_detailed(self, start_page, end_page):
        """
        SEW error code extraction: robustly handles multi-row error codes, suberrors, and merges split rows.
        Debug output removed for production use.
        """
        processed_errors = []
        current_error = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            start_idx = start_page - 1
            end_idx = end_page - 1

            if start_idx >= len(pdf.pages):
                logging.warning(f"Start page {start_page} is beyond the end of the document ({len(pdf.pages)} pages).")
                return []

            for i in range(start_idx, min(end_idx + 1, len(pdf.pages))):
                page = pdf.pages[i]
                table = page.extract_table()

                if not table:
                    continue

                for row in table:
                    if self.is_header_or_page_row(row):
                        continue

                    error_code = row[0]
                    suberror_code = row[1]
                    error_designation = row[2]
                    error_response = row[3]
                    possible_cause = row[4]
                    measure = row[5]

                    # --- State Machine Logic ---
                    # A new error code is identified by a non-empty value in the first column.
                    is_new_error = error_code and error_code.strip()
                    # A suberror is identified by a non-empty value in the second column, but an empty first column.
                    is_sub_error = suberror_code and suberror_code.strip() and not is_new_error

                    # --- Case 1: New Error Code Found ---
                    if is_new_error:
                        # If there's a previously accumulated error, save it before starting a new one.
                        if current_error:
                            processed_errors.append({
                                'error_code': self.clean_text(current_error.get('error_code', '')),
                                'suberror_code': self.clean_text(current_error.get('suberror_code', '')),
                                'error_designation': self.clean_text(current_error.get('error_designation', '')),
                                'error_response': self.clean_text(current_error.get('error_response', '')),
                                'possible_cause': self.clean_text(current_error.get('possible_cause', '')),
                                'measure': self.clean_text(current_error.get('measure', ''))
                            })
                        # Start a new error record.
                        current_error = {
                            'error_code': error_code,
                            'suberror_code': suberror_code,
                            'error_designation': error_designation,
                            'error_response': error_response,
                            'possible_cause': possible_cause,
                            'measure': measure
                        }
                    # --- Case 2: New Suberror Found ---
                    elif is_sub_error:
                        # Save the completed main error before starting a new record for the suberror.
                        if current_error:
                            processed_errors.append({
                                'error_code': self.clean_text(current_error.get('error_code', '')),
                                'suberror_code': self.clean_text(current_error.get('suberror_code', '')),
                                'error_designation': self.clean_text(current_error.get('error_designation', '')),
                                'error_response': self.clean_text(current_error.get('error_response', '')),
                                'possible_cause': self.clean_text(current_error.get('possible_cause', '')),
                                'measure': self.clean_text(current_error.get('measure', ''))
                            })
                        # Create a new record for the suberror, inheriting the last known error code.
                        current_error = {
                            'error_code': processed_errors[-1]['error_code'] if processed_errors else '',
                            'suberror_code': suberror_code,
                            'error_designation': error_designation,
                            'error_response': error_response,
                            'possible_cause': possible_cause,
                            'measure': measure
                        }
                    # --- Case 3: Continuation of a Previous Row ---
                    else:
                        # This row is a continuation of the previous one (either a main error or a suberror).
                        # Append the text from each cell to the corresponding field in the current error record.
                        if current_error:
                            current_error['error_designation'] = f"{current_error.get('error_designation', '')} {error_designation or ''}".strip()
                            current_error['error_response'] = f"{current_error.get('error_response', '')} {error_response or ''}".strip()
                            current_error['possible_cause'] = f"{current_error.get('possible_cause', '')} {possible_cause or ''}".strip()
                            current_error['measure'] = f"{current_error.get('measure', '')} {measure or ''}".strip()

        # After the loop, save the last accumulated error record.
        if current_error:
            processed_errors.append({
                'error_code': self.clean_text(current_error.get('error_code', '')),
                'suberror_code': self.clean_text(current_error.get('suberror_code', '')),
                'error_designation': self.clean_text(current_error.get('error_designation', '')),
                'error_response': self.clean_text(current_error.get('error_response', '')),
                'possible_cause': self.clean_text(current_error.get('possible_cause', '')),
                'measure': self.clean_text(current_error.get('measure', ''))
            })

        return processed_errors


class SEWDatabaseManager(DatabaseManager):
    """
    Extends DatabaseManager for detailed SEW error code table creation and insertion.
    """
    def create_sew_error_table_detailed(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS sew_error_codes_detailed")
        cursor.execute("""
            CREATE TABLE sew_error_codes_detailed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_code TEXT,
                error_designation TEXT,
                error_response TEXT,
                suberror_code TEXT,
                suberror_designation TEXT,
                possible_cause TEXT,
                measure TEXT
            )
        """)
        self.conn.commit()

    def insert_sew_error_codes_detailed(self, sew_errors):
        cursor = self.conn.cursor()
        for err in sew_errors:
            cursor.execute(
                "INSERT INTO sew_error_codes_detailed (error_code, error_designation, error_response, suberror_code, suberror_designation, possible_cause, measure) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    err["error_code"],
                    err["error_designation"],
                    err["error_response"],
                    err["suberror_code"],
                    err["suberror_designation"],
                    err["possible_cause"],
                    err["measure"]
                )
            )
        self.conn.commit()


def main():
    """
    Main function to run the PDF extraction and database insertion process.
    """
    setup_logging()
    # --- Configuration ---
    # The database will be created in the 'data' directory, one level above the script's 'src' directory.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    DB_PATH = os.path.join(data_dir, "errorCodesTechnologies.db")

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Extract tables from a PDF and store them in an SQLite database.")
    parser.add_argument("--pdf-path", required=True, help="Full path to the PDF file.")
    parser.add_argument("--table-name", required=True, help="Name of the table to store error codes.")
    parser.add_argument("--start-page", required=True, type=int, help="The first page to process (inclusive).")
    parser.add_argument("--end-page", required=True, type=int, help="The last page to process (inclusive).")
    parser.add_argument("--sew-mode", action="store_true", help="Enable SEW error code extraction mode.")
    args = parser.parse_args()

    logging.info("--- Starting PDF Processing ---")
    try:
        if args.sew_mode:
            extractor = SEWErrorCodeExtractor(args.pdf_path)
            sew_errors = extractor.extract_sew_error_codes_detailed(args.start_page, args.end_page)
            with SEWDatabaseManager(DB_PATH) as db:
                db.create_sew_error_table_detailed()
                db.insert_sew_error_codes_detailed(sew_errors)
            logging.info(f"Extracted and stored {len(sew_errors)} detailed SEW error codes.")
            return

        # 1. Extract data from PDF
        extractor = PDFTableExtractor(args.pdf_path)
        tables_data = extractor.extract_tables(args.start_page, args.end_page)

        if not tables_data:
            logging.warning("No tables were extracted. Exiting.")
            return

        # 2. Store data in the database
        with DatabaseManager(DB_PATH) as db:
            db.create_error_table(args.table_name)
            db.insert_table_data(args.table_name, tables_data)

        logging.info(f"--- Process Complete ---")
        logging.info(f"Data has been successfully stored in: {DB_PATH}")

    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    main()