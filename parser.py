import re
import fitz  # PyMuPDF
from typing import Dict, List
from dataclasses import dataclass, asdict
import json



@dataclass
class AssignmentMatch:
    """Stores information about a found assignment or date match."""
    text: str
    page_number: int
    context: str  # Surrounding text blurb
    match_type: str  # 'assignment' or 'date'
    position: tuple  # (x0, y0, x1, y1) bounding box coordinates

    def __str__(self):
        return f"""
            AssignmentMatch:
                Text: {self.text}
                Page: {self.page_number}
                Type: {self.match_type}
                Position: {self.position}
                Context: {self.context[:100]}...  # Truncate long context
            """


class PDFAssignmentParser:
    """
    A class that parses PDF documents to extract assignment information
    and dates using PyMuPDF.
    """
    
    def __init__(self, context_window: int = 200, assignment_threshold: float = 0.5):
        """
        Initialize the parser.
        
        Args:
            context_window: Number of characters to include before and after
                          a match when extracting context (default: 200)
            assignment_threshold: Confidence threshold for classifying real assignments (default: 0.5)
        """
        self.context_window = context_window
        self.assignment_threshold = assignment_threshold
        self.date_patterns = [
            # MM/DD/YYYY or MM-DD-YYYY
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            # Month DD, YYYY or Month DD YYYY
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            # Mon DD, YYYY or Mon DD YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b',
            # DD Month YYYY
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            # YYYY-MM-DD (ISO format)
            r'\b\d{4}-\d{2}-\d{2}\b',
            # Weekday, Month DD, YYYY
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        ]
        
        # Assignment keywords
        self.assignment_keywords = [
            r'\bassignment\b',
            r'\bassignments\b',
            r'\bdue\s+date\b',
            r'\bdue\b',
            r'\bhomework\b',
            r'\bproject\b',
            r'\bexam\b',
            r'\bfinal\b',
            r'\bmidterm\b',
            r'\bquiz\b',
            r'\blab\b',
        ]

        self.combined_date_pattern = re.compile(
                    '|'.join(f'({pattern})' for pattern in self.date_patterns),
                    re.IGNORECASE
                )
        
        self.assignment_pattern = re.compile(
            '|'.join(f'({keyword})' for keyword in self.assignment_keywords),
            re.IGNORECASE
        )
        
        # Positive indicators for real assignments
        self.positive_patterns = {
            'assignment_number': re.compile(
                r'\b(?:assignment|homework|hw|project|exam|quiz|lab)\s*[#:]?\s*\d+\b',
                re.IGNORECASE
            ),
            'action_verbs': re.compile(
                r'\b(?:submit|complete|turn\s+in|hand\s+in|due|hand\s+out|assign)\b',
                re.IGNORECASE
            ),
            'point_values': re.compile(
                r'\b(?:points?|pts?|worth|percent|%|grade)\b',
                re.IGNORECASE
            ),
            'capitalized_title': re.compile(
                r'\b(?:Assignment|Homework|Project|Exam|Quiz|Lab)\s+[A-Z][A-Za-z\s]+',
                re.IGNORECASE
            ),
            'list_format': re.compile(
                r'^[\s]*[•\-\*\d+\.]',  # Bullet points or numbered lists
                re.MULTILINE
            ),
        }
        
        # Negative indicators (false positives)
        self.negative_patterns = {
            'assignment_of': re.compile(
                r'\bassignment\s+of\s+(?:grades?|readings?|scores?|points?)\b',
                re.IGNORECASE
            ),
            'reading_assignment': re.compile(
                r'\breading\s+assignment\b',
                re.IGNORECASE
            ),
            'general_description': re.compile(
                r'\bassignment\s+(?:schedule|calendar|list|overview|summary)\b',
                re.IGNORECASE
            ),
        }
        
        # Scoring weights
        self.scoring_weights = {
            'assignment_number': 0.3,
            'due_date_proximity': 0.4,
            'action_verbs': 0.2,  # Per match, max 0.4
            'point_values': 0.2,
            'capitalized_title': 0.2,
            'list_format': 0.1,
            'specific_keywords': 0.1,
            'assignment_of': -0.8,
            'reading_assignment': -0.5,
            'general_description': -0.3,
        }
    
    def _extract_pages(self, pdf_path: str) -> tuple:
        """
        Extract all text from all pages of a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (document, list of page texts)
        """
        doc = fitz.open(pdf_path)
        page_texts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            page_texts.append(text)
        
        return doc, page_texts
    
    def _extract_context(self, text: str, match_start: int, match_end: int) -> str:
        """
        Extract surrounding context text around a match.
        
        Args:
            text: Full text to extract from
            match_start: Start position of the match
            match_end: End position of the match
            
        Returns:
            Context string with surrounding text
        """
        start_pos = max(0, match_start - self.context_window)
        end_pos = min(len(text), match_end + self.context_window)
        return text[start_pos:end_pos].strip()
    
    # MARK: do we even need this function
    def _is_real_assignment(self, match: AssignmentMatch, date_matches: List[AssignmentMatch] = None, threshold: float = None) -> tuple[bool, float]:
        """
        Determine if an assignment match is a real assignment task.
        
        Args:
            match: AssignmentMatch object to classify
            date_matches: Optional list of date matches to check for proximity
            threshold: Optional threshold override (uses self.assignment_threshold if None)
        
        Returns:
            Tuple of (is_real: bool, confidence_score: float)
        """
        if threshold is None:
            threshold = self.assignment_threshold
        
        context = match.context.lower()
        score = 0.0
        
        # Check for positive indicators
        # 1. Assignment numbering
        if self.positive_patterns['assignment_number'].search(context):
            score += self.scoring_weights['assignment_number']
        
        # 2. Due date proximity (check if date is within context)
        if date_matches:
            for date_match in date_matches:
                if date_match.page_number == match.page_number:
                    # Check if date appears in the context
                    if date_match.text.lower() in context:
                        score += self.scoring_weights['due_date_proximity']
                        break
        else:
            # Fallback: check if any date pattern appears in context
            if self.combined_date_pattern.search(context):
                score += self.scoring_weights['due_date_proximity']
        
        # 3. Action verbs (count matches, cap at max)
        action_verb_matches = len(self.positive_patterns['action_verbs'].findall(context))
        action_verb_score = min(action_verb_matches * self.scoring_weights['action_verbs'], 0.4)
        score += action_verb_score
        
        # 4. Point values
        if self.positive_patterns['point_values'].search(context):
            score += self.scoring_weights['point_values']
        
        # 5. Capitalized title
        if self.positive_patterns['capitalized_title'].search(match.context):  # Use original case
            score += self.scoring_weights['capitalized_title']
        
        # 6. List format
        if self.positive_patterns['list_format'].search(match.context):
            score += self.scoring_weights['list_format']
        
        # 7. Specific keywords (already matched, but add bonus)
        if any(kw in match.text.lower() for kw in ['homework', 'project', 'exam', 'quiz', 'lab']):
            score += self.scoring_weights['specific_keywords']
        
        # Check for negative indicators
        # 1. "assignment of"
        if self.negative_patterns['assignment_of'].search(context):
            score += self.scoring_weights['assignment_of']
        
        # 2. "reading assignment"
        if self.negative_patterns['reading_assignment'].search(context):
            score += self.scoring_weights['reading_assignment']
        
        # 3. General descriptions
        if self.negative_patterns['general_description'].search(context):
            score += self.scoring_weights['general_description']
        
        # Normalize score to 0.0-1.0 range
        # The maximum possible positive score is around 1.5 (all positive indicators)
        # The minimum possible score is around -1.6 (all negative indicators)
        # We'll normalize to 0.0-1.0 range using a linear transformation
        max_possible_score = 1.5
        min_possible_score = -1.6
        score_range = max_possible_score - min_possible_score
        
        # Normalize: shift to start at 0, then scale to 0-1
        normalized_score = max(0.0, min(1.0, (score - min_possible_score) / score_range))
        
        is_real = normalized_score >= threshold
        return (is_real, normalized_score)
    
    def _get_bounding_box(self, doc, page_num: int, match_text: str) -> tuple:
        """
        Get bounding box coordinates for a text match.
        
        Args:
            doc: PyMuPDF document object
            page_num: Page number (0-indexed)
            match_text: Text to find bounding box for
            
        Returns:
            Tuple of (x0, y0, x1, y1) coordinates, or (0, 0, 0, 0) if not found
        """
        try:
            page = doc[page_num]
            text_instances = page.search_for(match_text)
            if text_instances:
                rect = text_instances[0]
                # Convert Rect object to tuple
                return tuple(rect)  # Rect objects can be converted to tuple/list
            return (0, 0, 0, 0)
        except:
            return (0, 0, 0, 0)
    
    def _find_assignments(self, doc, page_texts: List[str]) -> List[AssignmentMatch]:
        """
        Find assignment keywords and extract context.
        
        Args:
            doc: PyMuPDF document object
            page_texts: List of text content for each page
            
        Returns:
            List of AssignmentMatch objects for found assignments
        """
        assignment_matches = []
        
        for page_num, text in enumerate(page_texts):
            for match in self.assignment_pattern.finditer(text):
                context = self._extract_context(text, match.start(), match.end())
                bbox = self._get_bounding_box(doc, page_num, match.group())
                
                assignment_match = AssignmentMatch(
                    text=match.group(),
                    page_number=page_num + 1,
                    context=context,
                    match_type='assignment',
                    position=bbox
                )
                assignment_matches.append(assignment_match)
        
        return assignment_matches
    
    def _find_dates(self, doc, page_texts: List[str]) -> List[AssignmentMatch]:
        """
        Find dates and extract context.
        
        Args:
            doc: PyMuPDF document object
            page_texts: List of text content for each page
            
        Returns:
            List of AssignmentMatch objects for found dates
        """
        date_matches = []
        
        for page_num, text in enumerate(page_texts):
            for match in self.combined_date_pattern.finditer(text):
                context = self._extract_context(text, match.start(), match.end())
                bbox = self._get_bounding_box(doc, page_num, match.group())
                
                date_match = AssignmentMatch(
                    text=match.group(),
                    page_number=page_num + 1,
                    context=context,
                    match_type='date',
                    position=bbox
                )
                date_matches.append(date_match)
        
        return date_matches
    
    def _find_combined_matches(self, page_texts: List[str], 
                               assignment_matches: List[AssignmentMatch],
                               date_matches: List[AssignmentMatch]) -> List[AssignmentMatch]:
        """
        Find combined matches where assignments and dates appear nearby.
        
        Args:
            page_texts: List of text content for each page
            assignment_matches: List of found assignment matches
            date_matches: List of found date matches
            
        Returns:
            List of AssignmentMatch objects for combined matches
        """
        combined_matches = []
        
        for page_num, text in enumerate(page_texts):
            # Get regex matches for this page
            assignment_regex_matches = list(self.assignment_pattern.finditer(text))
            date_regex_matches = list(self.combined_date_pattern.finditer(text))
            
            # Check if any assignment and date are within 300 characters of each other
            for assn_match in assignment_regex_matches:
                for date_match in date_regex_matches:
                    distance = abs(assn_match.start() - date_match.start())
                    if distance < 300:  # Within 300 characters
                        # Get combined context
                        start_pos = min(assn_match.start(), date_match.start())
                        end_pos = max(assn_match.end(), date_match.end())
                        context = self._extract_context(text, start_pos, end_pos)
                        
                        combined_match = AssignmentMatch(
                            text=f"{assn_match.group()} | {date_match.group()}",
                            page_number=page_num + 1,
                            context=context,
                            match_type='combined',
                            position=(0, 0, 0, 0)
                        )
                        combined_matches.append(combined_match)
                        break  # Only add once per assignment match
        
        return combined_matches
    
    def filter_real_assignments(self, assignment_matches: List[AssignmentMatch], 
                                date_matches: List[AssignmentMatch] = None) -> List[AssignmentMatch]:
        """
        Filter assignment matches to only include real assignments.
        
        Args:
            assignment_matches: List of AssignmentMatch objects to filter
            date_matches: Optional list of date matches for proximity checking
            
        Returns:
            List of AssignmentMatch objects that are classified as real assignments
        """
        real_assignments = []
        for match in assignment_matches:
            is_real, confidence = self._is_real_assignment(match, date_matches)
            if is_real:
                real_assignments.append(match)
        return real_assignments
    
    def extract_assignments_and_dates(self, pdf_path: str, filter_real: bool = False) -> Dict[str, List[AssignmentMatch]]:
        """
        Extract assignments and dates from a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            filter_real: If True, filter assignments to only include real assignments (default: False)
            
        Returns:
            Dictionary with keys:
            - 'assignments': List of AssignmentMatch objects where assignment keywords were found
            - 'dates': List of AssignmentMatch objects where dates were found
            - 'combined': List of AssignmentMatch objects where both assignment and date appear nearby
        """
        doc, page_texts = self._extract_pages(pdf_path)
        
        assignment_matches = self._find_assignments(doc, page_texts)
        date_matches = self._find_dates(doc, page_texts)
        
        # Filter assignments if requested
        if filter_real:
            assignment_matches = self.filter_real_assignments(assignment_matches, date_matches)
        
        combined_matches = self._find_combined_matches(page_texts, assignment_matches, date_matches)
        
        doc.close()
        
        return {
            'assignments': assignment_matches,
            'dates': date_matches,
            'combined': combined_matches
        }
    
    def get_assignments_with_confidence(self, pdf_path: str) -> List[Dict]:
        """
        Get assignments with confidence scores.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries with assignment info and confidence scores
        """
        doc, page_texts = self._extract_pages(pdf_path)
        assignment_matches = self._find_assignments(doc, page_texts)
        date_matches = self._find_dates(doc, page_texts)
        doc.close()
        
        assignments_with_confidence = []
        for match in assignment_matches:
            is_real, confidence = self._is_real_assignment(match, date_matches)
            assignments_with_confidence.append({
                'text': match.text,
                'page': match.page_number,
                'context': match.context,
                'is_real': is_real,
                'confidence': confidence,
                'position': match.position
            })
        
        return assignments_with_confidence
    
    def get_structured_data(self, pdf_path: str, filter_real: bool = False) -> Dict:
        """
        Get structured data in a format easier to process.
        
        Returns a dictionary with:
        - 'raw_matches': The full results from extract_assignments_and_dates
        - 'by_page': Matches organized by page number (with confidence and classification)
        - 'potential_assignments': List of dicts with assignment info, nearby dates, confidence, and classification
        
        Args:
            pdf_path: Path to the PDF file
            filter_real: If True, filter assignments to only include real assignments (default: False)
        """
        matches = self.extract_assignments_and_dates(pdf_path, filter_real=filter_real)
        
        # Calculate confidence and classification for all assignments
        # Use a helper function to get classification for a match
        def get_classification(assn_match):
            is_real, confidence = self._is_real_assignment(assn_match, matches['dates'])
            return {
                'is_real': is_real,
                'confidence': confidence,
                'confidence_percentage': confidence * 100
            }
        
        matches_dict = {
            'assignments': [
                {
                    **asdict(m),
                    **get_classification(m)
                }
                for m in matches['assignments']
            ],
            'dates': [asdict(m) for m in matches['dates']],
            'combined': [asdict(m) for m in matches['combined']]
        }

        # Organize by page (with confidence and classification)
        by_page = {}
        for match_type, match_list in matches.items():
            for match in match_list:
                page = match.page_number
                if page not in by_page:
                    by_page[page] = {'assignments': [], 'dates': [], 'combined': []}
                
                match_data = {
                    'text': match.text,
                    'context': match.context,
                    'position': match.position
                }
                
                # Add confidence and classification for assignments
                if match_type == 'assignments':
                    classification = get_classification(match)
                    match_data['is_real'] = classification['is_real']
                    match_data['confidence'] = classification['confidence']
                    match_data['confidence_percentage'] = classification['confidence_percentage']
                
                by_page[page][match_type].append(match_data)
        
        # Create potential assignments list (combining assignments with nearby dates, confidence, and classification)
        potential_assignments = []
        for combined in matches['combined']:
            # Find the assignment match that corresponds to this combined match
            assn_text = combined.text.split(' | ')[0] if ' | ' in combined.text else combined.text
            corresponding_assn = next(
                (a for a in matches['assignments'] if a.text == assn_text and a.page_number == combined.page_number),
                None
            )
            
            assignment_data = {
                'page': combined.page_number,
                'context': combined.context,
                'full_text': combined.text
            }
            
            if corresponding_assn:
                classification = get_classification(corresponding_assn)
                assignment_data['is_real'] = classification['is_real']
                assignment_data['confidence'] = classification['confidence']
                assignment_data['confidence_percentage'] = classification['confidence_percentage']
            
            potential_assignments.append(assignment_data)
        
        # Also add standalone assignments that might have dates nearby
        for assn in matches['assignments']:
            # Check if there's a date on the same page within context
            nearby_dates = [
                d for d in matches['dates']
                if d.page_number == assn.page_number
                and (d.context in assn.context or assn.context in d.context)
            ]
            if nearby_dates:
                classification = get_classification(assn)
                assignment_data = {
                    'page': assn.page_number,
                    'context': assn.context,
                    'assignment_text': assn.text,
                    'nearby_dates': [d.text for d in nearby_dates],
                    'is_real': classification['is_real'],
                    'confidence': classification['confidence'],
                    'confidence_percentage': classification['confidence_percentage']
                }
                
                potential_assignments.append(assignment_data)
        
        structured_data = {
            'raw_matches': matches,
            'by_page': by_page,
            'potential_assignments': potential_assignments
        }

        print(json.dumps(matches_dict, indent=4))
        return structured_data


print("Starting parser...")
try:
    parser = PDFAssignmentParser(assignment_threshold=0.6)
    parser.get_structured_data("AR 202 syllabus 2026.doc.pdf")
    print("Parser completed")
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()