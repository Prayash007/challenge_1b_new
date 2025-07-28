"import PyPDF2
import re
from pathlib import Path
import json


def extract_sections(pdf_path):
    """
    Extract text sections from PDF document.
    Optimized for BERT-based semantic ranking.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        list: List of section dictionaries with text and metadata
    """
    sections = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if not page_text.strip():
                        continue
                    
                    # Extract sections from this page
                    page_sections = parse_page_content(page_text, pdf_path, page_num)
                    sections.extend(page_sections)
                    
                except Exception as e:
                    print(f"Warning: Error processing page {page_num}: {e}")
                    continue
    
    except Exception as e:
        print(f"ERROR: Could not read PDF {pdf_path}: {e}")
        return []
    
    print(f"Extracted {len(sections)} sections from {Path(pdf_path).name}")
    return sections


def parse_page_content(text, pdf_path, page_num):
    """
    Parse page text into meaningful sections for BERT analysis.
    
    Args:
        text: Raw page text
        pdf_path: Source PDF path  
        page_num: Page number
        
    Returns:
        list: List of section dictionaries
    """
    sections = []
    
    # Clean and normalize text
    cleaned_text = normalize_text(text)
    
    # Multiple section detection strategies
    sections.extend(detect_heading_sections(cleaned_text, pdf_path, page_num))
    sections.extend(detect_recipe_sections(cleaned_text, pdf_path, page_num))
    sections.extend(detect_procedural_sections(cleaned_text, pdf_path, page_num))
    
    # If no structured sections found, create content blocks
    if not sections:
        sections = create_content_blocks(cleaned_text, pdf_path, page_num)
    
    return sections

def normalize_text(text):
    """
    Clean and normalize text for optimal BERT processing
    """
    # Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common PDF extraction issues
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add spaces between camelCase
    text = re.sub(r'(\d+)([A-Za-z])', r'\1 \2', text)  # Space between numbers and letters
    text = re.sub(r'([a-zA-Z])(\d+)', r'\1 \2', text)  # Space between letters and numbers
    
    # Clean up punctuation
    text = re.sub(r'\.{2,}', '.', text)  # Multiple dots to single
    text = re.sub(r'\s*\.\s*', '. ', text)  # Proper spacing around periods
    
    return text.strip()

def detect_heading_sections(text, pdf_path, page_num):
    """
    Detect sections based on heading patterns (optimized for BERT)
    """
    sections = []
    
    # Enhanced heading patterns for BERT
    heading_patterns = [
        r'^([A-Z][A-Z\s&]{3,}):?\s*$',  # ALL CAPS headings
        r'^(\d+\.?\d*\s+[A-Z][A-Za-z\s]{3,}):?\s*$',  # Numbered headings
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):?\s*$',  # Title Case headings
        r'^(Step\s+\d+[:\-]?\s*[A-Z][A-Za-z\s]+)$',  # Step headings
        r'^(Recipe[:\-]?\s*[A-Z][A-Za-z\s]+)$',  # Recipe headings
    ]
    
    lines = text.split('\n')
    current_section = None
    content_buffer = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line matches any heading pattern
        heading_match = None
        for pattern in heading_patterns:
            match = re.match(pattern, line)
            if match:
                heading_match = match.group(1).strip()
                break
        
        if heading_match:
            # Save previous section if exists
            if current_section and content_buffer:
                sections.append({
                    "document": Path(pdf_path).name,
                    "section_title": current_section,
                    "section_text": ' '.join(content_buffer),
                    "page_number": page_num,
                    "section_type": "heading_based"
                })
            
            # Start new section
            current_section = heading_match
            content_buffer = []
        else:
            # Add to content buffer
            if current_section:
                content_buffer.append(line)
    
    # Add final section
    if current_section and content_buffer:
        sections.append({
            "document": Path(pdf_path).name,
            "section_title": current_section,
            "section_text": ' '.join(content_buffer),
            "page_number": page_num,
            "section_type": "heading_based"
        })
    
    return sections

def detect_recipe_sections(text, pdf_path, page_num):
    """
    Detect recipe sections with enhanced patterns for BERT
    """
    sections = []
    
    # Recipe indicators
    recipe_patterns = [
        r'(?i)(ingredients?)\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=instructions?|directions?|method|preparation|\n\s*\n|$)',
        r'(?i)(instructions?|directions?|method|preparation)\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=ingredients?|notes?|\n\s*\n|$)',
        r'(?i)(serves?|serving|portions?)\s*:?\s*([^\n]+)',
        r'(?i)(cooking\s+time|prep\s+time|total\s+time)\s*:?\s*([^\n]+)',
    ]
    
    # Find recipe components
    for pattern in recipe_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
        for match in matches:
            title = match.group(1).strip().title()
            content = match.group(2).strip()
            
            if len(content) > 20:  # Minimum content length
                sections.append({
                    "document": Path(pdf_path).name,
                    "section_title": title,
                    "section_text": content,
                    "page_number": page_num,
                    "section_type": "recipe_component"
                })
    
    # Look for complete recipe blocks
    recipe_block_pattern = r'(?i)([A-Z][A-Za-z\s]+(?:recipe|dish|meal))\s*:?\s*([\s\S]+?)(?=(?:[A-Z][A-Za-z\s]+(?:recipe|dish|meal))|$)'
    recipe_matches = re.finditer(recipe_block_pattern, text)
    
    for match in recipe_matches:
        title = match.group(1).strip()
        content = match.group(2).strip()
        
        if len(content) > 100:  # Substantial recipe content
            sections.append({
                "document": Path(pdf_path).name,
                "section_title": title,
                "section_text": content[:500],  # Limit for BERT processing
                "page_number": page_num,
                "section_type": "complete_recipe"
            })
    
    return sections

def detect_procedural_sections(text, pdf_path, page_num):
    """
    Detect procedural/instructional sections for BERT processing
    """
    sections = []
    
    # Procedural patterns
    procedural_patterns = [
        r'(?i)(step\s+\d+[:\-]?\s*)([^\n]+(?:\n(?!\s*step\s+\d+)[^\n]+)*)',
        r'(?i)(\d+\.\s*)([^\n]+(?:\n(?!\s*\d+\.)[^\n]+)*)',
        r'(?i)(first|second|third|finally|next|then)[:\-]?\s*([^\n]+(?:\n[^\n]+)*?)(?=(?:first|second|third|finally|next|then)|\n\s*\n|$)',
    ]
    
    for pattern in procedural_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
        for match in matches:
            title = match.group(1).strip()
            content = match.group(2).strip()
            
            if len(content) > 30:  # Minimum content length
                sections.append({
                    "document": Path(pdf_path).name,
                    "section_title": f"Procedure: {title}",
                    "section_text": content,
                    "page_number": page_num,
                    "section_type": "procedural"
                })
    
    return sections

def create_content_blocks(text, pdf_path, page_num):
    """
    Create content blocks when no structured sections are found
    """
    sections = []
    
    # Split text into meaningful chunks (optimal for BERT)
    sentences = re.split(r'[.!?]+', text)
    
    current_block = []
    block_count = 1
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        current_block.append(sentence)
        
        # Create blocks of optimal size for BERT (150-300 words)
        if len(' '.join(current_block).split()) >= 150:
            block_text = '. '.join(current_block) + '.'
            
            # Create a meaningful title from first sentence
            title = current_block[0][:50] + "..." if len(current_block[0]) > 50 else current_block[0]
            
            sections.append({
                "document": Path(pdf_path).name,
                "section_title": f"Content Block {block_count}: {title}",
                "section_text": block_text,
                "page_number": page_num,
                "section_type": "content_block"
            })
            
            current_block = []
            block_count += 1
    
    # Add remaining content
    if current_block:
        block_text = '. '.join(current_block) + '.'
        title = current_block[0][:50] + "..." if len(current_block[0]) > 50 else current_block[0]
        
        sections.append({
            "document": Path(pdf_path).name,
            "section_title": f"Content Block {block_count}: {title}",
            "section_text": block_text,
            "page_number": page_num,
            "section_type": "content_block"
        })
    
    return sections

def extract_recipe_sections(pdf_path):
    """
    Specialized recipe extraction for food-related documents
    """
    sections = []
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if not text.strip():
                        continue
                    
                    # Enhanced recipe detection
                    recipe_sections = detect_individual_recipes(text, pdf_path, page_num)
                    sections.extend(recipe_sections)
                    
                except Exception as e:
                    print(f"⚠️  Error processing recipes on page {page_num}: {e}")
                    continue
    
    except Exception as e:
        print(f"❌ Error reading PDF for recipes {pdf_path}: {e}")
        return []
    
    print(f"🍳 Extracted {len(sections)} recipe sections from {Path(pdf_path).name}")
    return sections

def detect_individual_recipes(text, pdf_path, page_num):
    """
    Detect individual recipes with complete ingredient lists and instructions
    """
    sections = []
    
    # Pattern to find recipe titles
    recipe_title_patterns = [
        r'(?i)^([A-Z][A-Za-z\s]+(?:recipe|dish|meal|soup|salad|pasta|curry|chicken|beef|vegetarian|vegan))\s*$',
        r'(?i)([A-Z][A-Za-z\s]+)\s*-\s*(?:serves|cooking time|prep time)',
        r'(?i)(recipe\s+\d+[:\-]?\s*[A-Z][A-Za-z\s]+)',
    ]
    
    lines = text.split('\n')
    current_recipe = None
    recipe_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for recipe title
        title_match = None
        for pattern in recipe_title_patterns:
            match = re.search(pattern, line)
            if match:
                title_match = match.group(1).strip()
                break
        
        if title_match:
            # Save previous recipe
            if current_recipe and recipe_content:
                recipe_text = ' '.join(recipe_content)
                if len(recipe_text) > 50:  # Ensure substantial content
                    sections.append({
                        "document": Path(pdf_path).name,
                        "section_title": current_recipe,
                        "section_text": recipe_text,
                        "page_number": page_num,
                        "section_type": "individual_recipe"
                    })
            
            # Start new recipe
            current_recipe = title_match
            recipe_content = []
        else:
            # Add to current recipe content
            if current_recipe:
                recipe_content.append(line)
    
    # Add final recipe
    if current_recipe and recipe_content:
        recipe_text = ' '.join(recipe_content)
        if len(recipe_text) > 50:
            sections.append({
                "document": Path(pdf_path).name,
                "section_title": current_recipe,
                "section_text": recipe_text,
                "page_number": page_num,
                "section_type": "individual_recipe"
            })
    
    return sections

# Test function
def test_extraction():
    """Test the extraction functionality"""
    test_pdf = "input/file03.pdf"
    
    print("🧪 Testing BERT-optimized extraction...")
    sections = extract_sections(test_pdf)
    
    print(f"\n📊 Extraction Results:")
    print(f"   Total sections: {len(sections)}")
    
    # Show section types
    section_types = {}
    for section in sections:
        section_type = section.get('section_type', 'unknown')
        section_types[section_type] = section_types.get(section_type, 0) + 1
    
    print(f"   Section types:")
    for stype, count in section_types.items():
        print(f"     {stype}: {count}")
    
    # Show sample sections
    print(f"\n📝 Sample sections:")
    for i, section in enumerate(sections[:3]):
        print(f"   {i+1}. {section['section_title']}")
        print(f"      Type: {section.get('section_type', 'unknown')}")
        print(f"      Text: {section['section_text'][:100]}...")
        print()

if __name__ == "__main__":
    test_extraction()
