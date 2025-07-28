import os
import json
import time
import argparse
import datetime
from pathlib import Path

# Import our utility modules
import sys
sys.path.append('utils')

from extractor import extract_sections
from ranker import rank_sections


def process_collection(collection_path, args=None):
    """
    Process a single document collection using BERT ranking.
    
    Args:
        collection_path: Path to collection directory
        args: Command line arguments (optional)
        
    Returns:
        bool: True if processing successful, False otherwise
    """
    collection_name = os.path.basename(collection_path)
    print(f"\n=== CHALLENGE 1B: {collection_name.upper()} ===")
    print("BERT-based Document Ranking System")
    print("-" * 60)
    
    # Load collection configuration
    input_file = os.path.join(collection_path, "challenge1b_input.json")
    
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read input file: {e}")
        return False
    
    # Display scenario information
    print(f"Challenge: {input_data['challenge_info']['description']}")
    print(f"Persona: {input_data['persona']['role']}")
    print(f"Task: {input_data['job_to_be_done']['task']}")
    print("-" * 60)
    
    # Process PDF documents
    pdf_directory = os.path.join(collection_path, "PDFs")
    all_sections = []
    
    print("Loading BERT system...")
    start_time = time.time()
    
    for document in input_data['documents']:
        pdf_path = os.path.join(pdf_directory, document['filename'])
        print(f"\nProcessing: {document['title']}")
        
        if os.path.exists(pdf_path):
            try:
                sections = extract_sections(pdf_path)
                # Tag each section with source document
                for section in sections:
                    section['document'] = document['filename']
                print(f"  -> Extracted {len(sections)} sections")
                all_sections.extend(sections)
            except Exception as e:
                print(f"  -> ERROR: {str(e)}")
        else:
            print(f"  -> ERROR: File not found: {pdf_path}")
    
    extraction_time = time.time() - start_time
    print(f"\nExtraction complete:")
    print(f"  Total sections: {len(all_sections)}")
    print(f"  Processing time: {extraction_time:.2f} seconds")
    
    if not all_sections:
        print("ERROR: No sections extracted - cannot proceed with ranking")
        return False
    
    # Run BERT ranking
    print("\nRunning BERT ranking...")
    ranking_start = time.time()
    
    # Use persona and job description for ranking
    persona = input_data['persona']['role']
    job_description = input_data['job_to_be_done']['task']
    
    ranked_results, subsection_analysis = rank_sections(all_sections, persona, job_description)
    
    ranking_time = time.time() - ranking_start
    print(f"⏱️  BERT ranking time: {ranking_time:.2f} seconds")
    print(f"🚀 Processing speed: {len(all_sections)/ranking_time:.1f} sections/second")
    
    # Create output JSON file
    if args and args.docker:
        # Docker environment - write to mounted output directory  
        collection_num = os.path.basename(collection_path).split()[-1]
        output_json = os.path.join('/app/output', f'Collection_{collection_num}_output.json')
    else:
        # Local environment - write to collection directory
        output_json = os.path.join(collection_path, 'challenge1b_output.json')
    
    # Build output in the same format as original Challenge 1B
    metadata = {
        'input_documents': [d['filename'] for d in input_data['documents']],
        'persona': persona,
        'job_to_be_done': job_description,
        'processing_timestamp': datetime.datetime.now().isoformat(),
        'model_type': 'BERT (RoBERTa-Base)',
        'processing_time_seconds': ranking_time + extraction_time,
        'sections_processed': len(all_sections),
        'sections_ranked': len(ranked_results)
    }
    
    output_data = {
        'metadata': metadata,
        'extracted_sections': ranked_results,
        'subsection_analysis': subsection_analysis if subsection_analysis else []
    }
    
    # Write output JSON
    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Output written to: {output_json}")
        print(f"📝 Total ranked sections: {len(ranked_results)}")
    except Exception as e:
        print(f"⚠️  Warning: Could not write output file: {e}")
    
    # Display top results
    print("\n🏆 TOP 10 BERT RANKED RESULTS:")
    print("=" * 80)
    
    for i, section in enumerate(ranked_results[:10], 1):
        title = section.get('section_title', 'Untitled')
        text = section.get('section_text', '')
        
        print(f"\n{i}. TITLE: {title}")
        print(f"   SOURCE: {section.get('document', section.get('source', 'Unknown'))}")
        print(f"   CONTENT: {text[:200]}...")
        if len(text) > 200:
            print("   [Content truncated for display]")
    
    # Print top 3 sections for verification (like original)
    print(f"\n📋 TOP 3 SECTIONS SUMMARY:")
    for i, section in enumerate(ranked_results[:3], 1):
        document = section.get('document', 'Unknown')
        title = section.get('section_title', 'Untitled')
        page = section.get('page_number', 'N/A')
        print(f"{i}. [{document}] {title} (Page {page})")
    
    # Summary statistics
    total_time = time.time() - start_time
    print(f"\n📈 PERFORMANCE SUMMARY:")
    print(f"   Collection: {collection_name}")
    print(f"   Total Processing Time: {total_time:.2f} seconds")
    print(f"   Documents Processed: {len(input_data['documents'])}")
    print(f"   Sections Extracted: {len(all_sections)}")
    print(f"   Average Section Length: {sum(len(s.get('section_text', '')) for s in all_sections) / len(all_sections):.0f} chars")
    print(f"   BERT Model: RoBERTa-Base")
    
    print(f"\n🎉 BERT processing on {collection_name} complete!")
    return True

def main():
    """
    Main function to process Challenge 1B collections with BERT.
    """
    parser = argparse.ArgumentParser(description='Challenge 1B: BERT-based document ranking')
    parser.add_argument('--collection', type=str, help='Specific collection to process (1, 2, 3, etc.)')
    parser.add_argument('--all', action='store_true', help='Process all available collections')
    parser.add_argument('--docker', action='store_true', help='Running in Docker environment')
    
    args = parser.parse_args()
    
    # Determine base directory (Docker vs local)
    if args.docker or os.path.exists('/app/collections'):
        # Docker environment
        base_dir = '/app/collections'
        output_base = '/app/output'
        print("🐳 Running in Docker environment")
    else:
        # Local environment
        base_dir = os.path.dirname(__file__)
        output_base = base_dir
        print("💻 Running in local environment")
    
    collections = []
    
    if args.collection:
        collection_path = os.path.join(base_dir, f'Collection {args.collection}')
        if os.path.exists(collection_path):
            collections.append(collection_path)
        else:
            print(f"❌ Collection {args.collection} not found")
            return
    elif args.all:
        # Find all available collections
        for item in os.listdir(base_dir):
            if item.startswith('Collection ') and os.path.isdir(os.path.join(base_dir, item)):
                collections.append(os.path.join(base_dir, item))
        collections.sort()  # Sort to process in order
    else:
        # Default: process Collection 1
        collection_path = os.path.join(base_dir, 'Collection 1')
        if os.path.exists(collection_path):
            collections.append(collection_path)
        else:
            print("❌ No Collection 1 found. Use --collection <number> or --all")
            return
    
    if not collections:
        print("❌ No collections found to process")
        return
    
    print(f"🚀 Challenge 1B BERT: Processing {len(collections)} collection(s)...")
    
    success_count = 0
    for collection_path in collections:
        print(f"\n{'='*80}")
        if process_collection(collection_path, args):
            success_count += 1
        print(f"{'='*80}")
    
    print(f"\n🏆 Challenge 1B completed! Successfully processed {success_count}/{len(collections)} collections.")

if __name__ == "__main__":
    main()
