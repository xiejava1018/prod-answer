"""
CSV file parser implementation.
"""
from typing import List, Dict
import csv
from .base import BaseFileParser


class CSVParser(BaseFileParser):
    """
    Parser for CSV files.
    Supports various delimiters and encodings.
    """

    def __init__(self, delimiter: str = ',', encoding: str = 'utf-8'):
        """
        Initialize CSV parser.

        Args:
            delimiter: CSV delimiter character (default: comma)
            encoding: File encoding (default: utf-8)
        """
        self.delimiter = delimiter
        self.encoding = encoding

    def parse(self, file_path: str) -> List[Dict]:
        """
        Parse CSV file and extract data.

        Args:
            file_path: Path to CSV file

        Returns:
            List of dictionaries (one per row)
        """
        try:
            data = []

            with open(file_path, 'r', encoding=self.encoding, newline='') as f:
                # Try to detect delimiter
                dialect = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)

                reader = csv.DictReader(f, dialect=dialect)

                for row in reader:
                    # Remove empty values
                    row_data = {
                        k: v.strip() if v else ''
                        for k, v in row.items()
                        if v is not None
                    }

                    # Only add if row has some data
                    if any(v.strip() for v in row_data.values() if v):
                        data.append(row_data)

            return data

        except csv.Sniffer.Error:
            # If sniffing fails, try with default delimiter
            with open(file_path, 'r', encoding=self.encoding, newline='') as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)

                data = []
                for row in reader:
                    row_data = {
                        k: v.strip() if v else ''
                        for k, v in row.items()
                        if v is not None
                    }

                    if any(v.strip() for v in row_data.values() if v):
                        data.append(row_data)

                return data

        except Exception as e:
            raise ValueError(f"Failed to parse CSV file: {str(e)}")

    def extract_requirements(self, parsed_data: List[Dict]) -> List[str]:
        """
        Extract requirements from CSV data.

        Uses same logic as Excel parser.
        """
        requirements = []

        for item in parsed_data:
            requirement_text = None
            for key in ['requirement', 'requirement_text', 'feature', 'capability',
                       'description', 'text', 'content', 'name', 'title']:
                if key in item and item[key] and item[key].strip():
                    requirement_text = item[key].strip()
                    break

            if not requirement_text:
                for value in item.values():
                    if value and value.strip():
                        requirement_text = value.strip()
                        break

            if requirement_text:
                requirements.append(requirement_text)

        return requirements
