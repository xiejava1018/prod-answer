"""
Base class for file parsers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict


class BaseFileParser(ABC):
    """
    Abstract base class for file parsers.
    All file parsers should inherit from this class.
    """

    @abstractmethod
    def parse(self, file_path: str) -> List[Dict]:
        """
        Parse file and return list of data dictionaries.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of dictionaries containing parsed data
        """
        pass

    def extract_requirements(self, parsed_data: List[Dict]) -> List[str]:
        """
        Extract requirement texts from parsed data.

        Args:
            parsed_data: List of dictionaries from parse()

        Returns:
            List of requirement text strings
        """
        requirements = []

        for item in parsed_data:
            # Try to find requirement text in common fields
            for key in ['requirement', 'description', 'feature', 'capability', 'text', 'content']:
                if key in item and item[key]:
                    requirements.append(str(item[key]).strip())
                    break
            else:
                # If no standard field found, join all values
                if item:
                    text = ' '.join([str(v) for v in item.values() if v])
                    if text.strip():
                        requirements.append(text.strip())

        return requirements

    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file can be parsed.

        Args:
            file_path: Path to the file

        Returns:
            True if file is valid
        """
        try:
            self.parse(file_path)
            return True
        except Exception:
            return False
