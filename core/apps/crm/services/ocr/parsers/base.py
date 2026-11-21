"""
Abstract Base Class for Document Parsers.
"""

import abc
from typing import Any


class BaseDocumentParser(abc.ABC):
    """
    Abstract interface for parsing and extracting structured data from document text.
    """

    doc_type: str = ""

    @abc.abstractmethod
    def parse(self, text: str, mask: bool = False) -> dict[str, Any]:
        """
        Parse raw document text into structured fields.

        Args:
            text (str): Document text block.
            mask (bool): Optional flag to mask sensitive PII numbers. Defaults to False.

        Returns:
            dict[str, Any]: Extracted document fields.
        """
