import pdfplumber
import sqlite3
import os
import argparse


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
        print(f"Opening PDF: {os.path.basename(self.pdf_path)}")
        with pdfplumber.open(self.pdf_path) as pdf:
            # Adjust for 0-based indexing used by pdfplumber
            start_idx = start_page - 1
            end_idx = end_page - 1

            if start_idx >= len(pdf.pages):
                print(f"Error: Start page {start_page} is beyond the end of the document ({len(pdf.pages)} pages).")
                return []

            print(f"Processing pages from {start_page} to {end_page}...")
            for i in range(start_idx, min(end_idx + 1, len(pdf.pages))):
                page = pdf.pages[i]
                tables = page.extract_tables()
                if tables:
                    print(f"  - Found {len(tables)} table(s) on page {i + 1}.")
                    # Clean up the data by removing None and replacing newlines
                    for table in tables:
                        cleaned_table = []
                        for row in table:
                            cleaned_row = [str(cell).replace('\n', ' ') if cell is not None else "" for cell in row]
                            cleaned_table.append(cleaned_row)
                        all_tables_data.append(cleaned_table)
                else:
                    print(f"  - No tables found on page {i + 1}.")
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

    def create_error_table(self, table_name):
        """
        Creates a table with the given name if it doesn't already exist.
        The table has a flexible number of columns to accommodate different table structures.

        Args:
            table_name (str): The name for the new table.
        """
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
        print(f"Database '{os.path.basename(self.db_path)}' is ready. Table '{table_name}' created.")

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
        print(f"Successfully inserted {total_rows_inserted} rows into the '{table_name}' table.")


def main():
    """
    Main function to run the PDF extraction and database insertion process.
    """
    # --- Configuration ---
    # The database will be created in the same directory as the script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(script_dir, "errorCodesTechnologies.db")

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Extract tables from a PDF and store them in an SQLite database.")
    parser.add_argument("--pdf-path", required=True, help="Full path to the PDF file.")
    parser.add_argument("--table-name", required=True, help="Name of the table to store error codes.")
    parser.add_argument("--start-page", required=True, type=int, help="The first page to process (inclusive).")
    parser.add_argument("--end-page", required=True, type=int, help="The last page to process (inclusive).")
    args = parser.parse_args()

    print("--- Starting PDF Processing ---")
    try:
        # 1. Extract data from PDF
        extractor = PDFTableExtractor(args.pdf_path)
        tables_data = extractor.extract_tables(args.start_page, args.end_page)

        if not tables_data:
            print("No tables were extracted. Exiting.")
            return

        # 2. Store data in the database
        with DatabaseManager(DB_PATH) as db:
            db.create_error_table(args.table_name)
            db.insert_table_data(args.table_name, tables_data)

        print(f"--- Process Complete ---")
        print(f"Data has been successfully stored in: {DB_PATH}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
