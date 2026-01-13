"""
Excel file parser implementation.
"""
from typing import List, Dict
import openpyxl
from .base import BaseFileParser


class ExcelParser(BaseFileParser):
    """
    Parser for Excel files (.xlsx, .xls).
    Expects data in tabular format with headers.
    """

    def parse(self, file_path: str) -> List[Dict]:
        """
        Parse Excel file and extract data.

        Args:
            file_path: Path to Excel file

        Returns:
            List of dictionaries (one per row)
        """
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active

            data = []
            headers = None

            for row_idx, row in enumerate(sheet.iter_rows(values_only=True), 1):
                # First row contains headers
                if row_idx == 1:
                    headers = [str(cell) if cell is not None else f'column_{i}'
                              for i, cell in enumerate(row)]
                    continue

                # Skip empty rows
                if all(cell is None or str(cell).strip() == '' for cell in row):
                    continue

                # Create dictionary for this row
                row_data = {}
                for col_idx, value in enumerate(row):
                    if col_idx < len(headers):
                        key = headers[col_idx]
                        # Convert value to string if not None
                        row_data[key] = str(value) if value is not None else ''

                # Only add if row has some data
                if any(v.strip() for v in row_data.values() if v):
                    data.append(row_data)

            return data

        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {str(e)}")

    def extract_requirements(self, parsed_data: List[Dict]) -> List[str]:
        """
        Extract requirements from Excel data.

        Looks for common column names like 'requirement', 'feature', etc.
        """
        requirements = []

        for item in parsed_data:
            # Try common column names
            requirement_text = None
            for key in ['requirement', 'requirement_text', 'feature', 'capability',
                       'description', 'text', 'content', 'name', 'title']:
                if key in item and item[key] and item[key].strip():
                    requirement_text = item[key].strip()
                    break

            # If no standard column found, use the first non-empty value
            if not requirement_text:
                for value in item.values():
                    if value and value.strip():
                        requirement_text = value.strip()
                        break

            if requirement_text:
                requirements.append(requirement_text)

        return requirements
