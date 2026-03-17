"""
Spreadsheet Parser Service

This service provides functionality to parse student data from various
spreadsheet formats (CSV, XLSX, ODS) for bulk enrollment operations.

BUSINESS CONTEXT:
Instructors can upload spreadsheets containing student information to
quickly enroll multiple students in courses or tracks. This service
extracts and normalizes student data from different file formats.

SUPPORTED FORMATS:
- CSV (Comma-Separated Values)
- XLSX (Microsoft Excel)
- ODS (LibreOffice Calc)

REQUIRED COLUMNS:
- email (REQUIRED): Student email address for account creation
- first_name (OPTIONAL): Student first name
- last_name (OPTIONAL): Student last name
- role (OPTIONAL): Defaults to 'student'

USAGE EXAMPLE:
    parser = SpreadsheetParser()
    students = parser.parse_csv(csv_content)
    for student in students:
        print(student['email'])
"""
import pandas as pd
import io
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class SpreadsheetParser:
    """
    Service for parsing student data from spreadsheet files.

    BUSINESS REQUIREMENTS:
    - Support multiple file formats (CSV, XLSX, ODS)
    - Extract student data with flexible column mapping
    - Handle missing optional columns gracefully
    - Validate required columns are present
    - Provide descriptive error messages
    """

    REQUIRED_COLUMNS = ['email']
    OPTIONAL_COLUMNS = ['first_name', 'last_name', 'role']
    DEFAULT_ROLE = 'student'

    def parse_csv(self, csv_content: str) -> List[Dict]:
        """
        Parse student data from CSV content.

        BUSINESS LOGIC:
        - Read CSV string into pandas DataFrame
        - Validate required columns exist
        - Convert to list of dictionaries
        - Apply default values for missing optional fields

        Args:
            csv_content: CSV file content as string

        Returns:
            List of dictionaries containing student data

        Raises:
            ValueError: If CSV is empty or missing required columns
        """
        if not csv_content or not csv_content.strip():
            raise ValueError("Empty spreadsheet")

        try:
            # Parse CSV content
            df = pd.read_csv(io.StringIO(csv_content))

            # Validate and process
            return self._process_dataframe(df)

        except pd.errors.EmptyDataError:
            raise ValueError("Empty spreadsheet")
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise ValueError(f"Failed to parse CSV: {str(e)}")

    def parse_xlsx(self, xlsx_bytes: bytes) -> List[Dict]:
        """
        Parse student data from XLSX binary content.

        BUSINESS LOGIC:
        - Read XLSX bytes into pandas DataFrame using openpyxl engine
        - Validate required columns exist
        - Convert to list of dictionaries
        - Apply default values for missing optional fields

        Args:
            xlsx_bytes: XLSX file content as bytes

        Returns:
            List of dictionaries containing student data

        Raises:
            ValueError: If XLSX is empty or missing required columns
        """
        if not xlsx_bytes:
            raise ValueError("Empty spreadsheet")

        try:
            # Parse XLSX content
            df = pd.read_excel(io.BytesIO(xlsx_bytes), engine='openpyxl')

            # Validate and process
            return self._process_dataframe(df)

        except Exception as e:
            logger.error(f"Error parsing XLSX: {e}")
            raise ValueError(f"Failed to parse XLSX: {str(e)}")

    def parse_ods(self, ods_bytes: bytes) -> List[Dict]:
        """
        Parse student data from ODS binary content.

        BUSINESS LOGIC:
        - Read ODS bytes into pandas DataFrame using odf engine
        - Validate required columns exist
        - Convert to list of dictionaries
        - Apply default values for missing optional fields

        Args:
            ods_bytes: ODS file content as bytes

        Returns:
            List of dictionaries containing student data

        Raises:
            ValueError: If ODS is empty or missing required columns
        """
        if not ods_bytes:
            raise ValueError("Empty spreadsheet")

        try:
            # Parse ODS content
            df = pd.read_excel(io.BytesIO(ods_bytes), engine='odf')

            # Validate and process
            return self._process_dataframe(df)

        except Exception as e:
            logger.error(f"Error parsing ODS: {e}")
            raise ValueError(f"Failed to parse ODS: {str(e)}")

    def _process_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        """
        Process pandas DataFrame into list of student dictionaries.

        BUSINESS LOGIC:
        - Validate required columns are present
        - Apply default values for missing optional columns
        - Convert DataFrame to list of dictionaries
        - Clean and normalize data

        Args:
            df: Pandas DataFrame containing student data

        Returns:
            List of dictionaries containing normalized student data

        Raises:
            ValueError: If required columns are missing
        """
        if df.empty:
            raise ValueError("Empty spreadsheet")

        # Validate required columns
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required column: {missing_columns[0]}")

        # Add default values for missing optional columns
        for col in self.OPTIONAL_COLUMNS:
            if col not in df.columns:
                if col == 'role':
                    df[col] = self.DEFAULT_ROLE
                else:
                    df[col] = None

        # Convert to list of dictionaries
        students = df.to_dict('records')

        # Clean data (strip whitespace, handle NaN)
        cleaned_students = []
        for student in students:
            cleaned_student = {}
            for key, value in student.items():
                if pd.isna(value):
                    cleaned_student[key] = None if key != 'role' else self.DEFAULT_ROLE
                elif isinstance(value, str):
                    cleaned_student[key] = value.strip()
                else:
                    cleaned_student[key] = value
            cleaned_students.append(cleaned_student)

        logger.info(f"Parsed {len(cleaned_students)} students from spreadsheet")
        return cleaned_students

    def detect_format(self, file_content: bytes, filename: str) -> str:
        """
        Detect spreadsheet format from filename or content.

        BUSINESS LOGIC:
        - Use file extension to determine format
        - Fall back to content-based detection if needed

        Args:
            file_content: File content as bytes
            filename: Original filename with extension

        Returns:
            Format string: 'csv', 'xlsx', or 'ods'

        Raises:
            ValueError: If format cannot be determined
        """
        extension = filename.lower().split('.')[-1]

        if extension == 'csv':
            return 'csv'
        elif extension in ['xlsx', 'xls']:
            return 'xlsx'
        elif extension == 'ods':
            return 'ods'
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    def parse_file(self, file_content: bytes, filename: str) -> List[Dict]:
        """
        Parse spreadsheet file automatically detecting format.

        BUSINESS LOGIC:
        - Detect file format from filename
        - Route to appropriate parser method
        - Return normalized student data

        Args:
            file_content: File content as bytes or string
            filename: Original filename with extension

        Returns:
            List of dictionaries containing student data

        Raises:
            ValueError: If format is unsupported or parsing fails
        """
        format_type = self.detect_format(file_content, filename)

        if format_type == 'csv':
            # Convert bytes to string for CSV
            csv_content = file_content.decode('utf-8') if isinstance(file_content, bytes) else file_content
            return self.parse_csv(csv_content)
        elif format_type == 'xlsx':
            return self.parse_xlsx(file_content)
        elif format_type == 'ods':
            return self.parse_ods(file_content)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
