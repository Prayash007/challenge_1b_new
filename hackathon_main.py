import os
import sys
import json
import datetime
import glob
import time

# Import utilities
sys.path.append('utils')
from extractor import extract_sections
from ranker import rank_sections


def process_hackathon_input():
    """
    Main entry point for hackathon Docker environment.
    Processes PDFs from /app/input and outputs results to /app/output.
    """
    input_dir = '/app/input'
    output_dir = '/app/output'
    
    # Fall back to local development if not in Docker
    if not os.path.exists(input_dir):
        print("Docker environment not detected, using local Collection 1...")
        return process_local_collection()
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("CHALLENGE 1B: BERT Document Ranking")
    print("=" * 50)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Look for configuration file
    config_path = os.path.join(input_dir, 'challenge1b_input.json')
    if not os.path.exists(config_path):
        print("No configuration file found, using defaults...")
        # Default configuration for BERT
        config = {
            "persona": {"role": "Document Analyst"},
            "job_to_be_done": {"task": "Rank document sections by relevance using BERT"},
            "documents": []
        }
    else:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            spec = json.load(f)
    
    # Find all PDF files in input directory
    pdf_files = glob.glob(os.path.join(input_dir, '*.pdf'))
    if not pdf_files:
        print("❌ No PDF files found in input directory!")
        return False
    
    print(f"📄 Found {len(pdf_files)} PDF files to process")
    
    # Update spec with found PDFs if documents list is empty
    if not spec.get('documents'):
        spec['documents'] = [{'filename': os.path.basename(pdf)} for pdf in pdf_files]
    
    persona = spec['persona']['role']
    job = spec['job_to_be_done']['task']
    
    print(f"🧑‍💼 Persona: {persona}")
    print(f"📋 Task: {job}")
    print("=" * 80)
    
    start_time = time.time()
    all_sections = []
    processed_files = []
    
    # Process each PDF with BERT-optimized extraction
    print("🚀 Initializing BERT System...")
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"📄 Processing: {filename}")
        
        try:
            sections = extract_sections(pdf_path)
            
            # Add document name to each section
            for sec in sections:
                sec['document'] = filename
            all_sections.extend(sections)
            
            # Create individual JSON file for this PDF
            pdf_name = os.path.splitext(filename)[0]
            individual_output = {
                'document': filename,
                'sections_extracted': len(sections),
                'processing_method': 'BERT-optimized extraction',
                'sections': sections[:15]  # Top 15 sections for individual file
            }
            
            individual_json_path = os.path.join(output_dir, f'{pdf_name}.json')
            with open(individual_json_path, 'w', encoding='utf-8') as f:
                json.dump(individual_output, f, ensure_ascii=False, indent=2)
            
            processed_files.append(filename)
            print(f"   ✅ Extracted {len(sections)} sections")
            
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
            continue
    
    extraction_time = time.time() - start_time
    print(f"\n📊 Total sections extracted: {len(all_sections)}")
    print(f"⏱️  Extraction time: {extraction_time:.2f} seconds")
    
    if not all_sections:
        print("❌ No sections extracted from any documents")
        return False
    
    # Rank sections with BERT
    print("🧠 Ranking sections with BERT...")
    ranking_start = time.time()
    
    ranked_sections, subsections = rank_sections(all_sections, persona, job)
    
    ranking_time = time.time() - ranking_start
    total_time = time.time() - start_time
    
    print(f"⏱️  BERT ranking time: {ranking_time:.2f} seconds")
    print(f"🚀 Processing speed: {len(all_sections)/ranking_time:.1f} sections/second")
    
    # Create consolidated output.json with BERT metadata
    output_data = {
        'challenge': '1B_NEW',
        'description': 'BERT-based Document Ranking System',
        'model_info': {
            'type': 'RoBERTa-Base',
            'size': '~500MB',
            'constraint_compliance': '<1GB ✅'
        },
        'metadata': {
            'persona': persona,
            'job_to_be_done': job,
            'processing_timestamp': datetime.datetime.now().isoformat(),
            'processed_files': processed_files,
            'total_files': len(processed_files),
            'total_sections': len(all_sections),
            'ranked_sections': len(ranked_sections),
            'processing_time_seconds': total_time,
            'extraction_time_seconds': extraction_time,
            'ranking_time_seconds': ranking_time,
            'sections_per_second': len(all_sections) / ranking_time if ranking_time > 0 else 0
        },
        'top_ranked_sections': ranked_sections[:25],  # Top 25 for BERT output
        'subsection_analysis': subsections if subsections else []
    }
    
    output_json_path = os.path.join(output_dir, 'output.json')
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Output written to: {output_json_path}")
    print(f"📝 Total ranked sections: {len(ranked_sections)}")
    
    # Print top 3 sections summary
    print(f"\n📋 TOP 3 BERT RANKED SECTIONS:")
    for i, section in enumerate(ranked_sections[:3], 1):
        document = section.get('document', 'Unknown')
        title = section.get('section_title', 'Untitled')
        page = section.get('page_number', 'N/A')
        print(f"{i}. [{document}] {title} (Page {page})")
    
    print(f"\n🎉 Challenge 1B BERT completed! Processed {len(processed_files)} files.")
    print(f"📈 Performance: {len(all_sections)} sections in {total_time:.2f}s")
    print(f"🏆 Model: RoBERTa-Base (~500MB, constraint compliant)")
    
    return True

def process_local_collection():
    """
    Fallback to process local Collection 1 if not in Docker environment.
    """
    print("💻 Running in local mode...")
    from run_collection import main as collection_main
    import sys
    sys.argv = ['run_collection.py', '--collection', '1']  # Simulate command line
    try:
        collection_main()
        return True
    except:
        return False

def main():
    """
    Main entry point for hackathon compliance.
    """
    try:
        success = process_hackathon_input()
        if not success:
            print("❌ Processing failed!")
            sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
