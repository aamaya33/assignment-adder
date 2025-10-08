import pymupdf


class FileIngestor:
    """
    Class that handles file ingestion. The files are typically pdf, xml
    with assignments and due dates 

    this function will parse the files and extract the assignment and due date
    to feed into a service that is able to add it to the calendar within calendar_service.py


    """

    def read_and_extract_from_file(self, file_path: str) -> dict:
        """
        Ingest the file and extract relevant information.

        Args:
            None

        Returns:
            Extracted information from the file.
        """
        doc = pymupdf.open(file_path)
        page = doc.load_page(0)
        print(type(page), page.get_contents())
        return {}

    def parse_pdf_content(self, file_content: dict) -> dict:
        """
        Parse the content of a PDF file and identifies assignements and due 
        dates

        Args:
            file_content (dict): The content of the PDF file.

        Returns:
            dict: Parsed information from the PDF.
        """
        return {}

    def _extract_date_ranges(self, file_content: dict) -> list:
        """
        Extract date ranges from the file content.

        Args:
            file_content (dict): The content of the file.

        Returns:
            list: A list of extracted date ranges.
        """
        return []

    def _extract_assignements(self, file_content: dict) -> list:
        """
        Extract assignments from the file content.

        Args:
            file_content (dict): The content of the file.

        Returns:
            list: A list of extracted assignments.
        """
        return []

test = FileIngestor()
test.read_and_extract_from_file("C:\\Users\\amaya\\Documents\\GitHub\\park-finder\\src\\backend\\services\\file_ingestion\\CourseSchedule-CC-25-fall.pdf")
