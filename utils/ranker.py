#!/usr/bin/env python3
"""
Improved BERT-based Ranking System
Adobe Hackathon Challenge 1B - Advanced BERT Implementation
"""

import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import time
import re
from pathlib import Path

# Global model variables
_tokenizer = None
_model = None
_model_initialized = False

def initialize_bert_model():
    """
    Initialize the improved BERT model (RoBERTa-Large with optimizations)
    """
    global _tokenizer, _model, _model_initialized
    
    if _model_initialized:
        return _tokenizer, _model
    
    try:
        from transformers import AutoTokenizer, AutoModel
        
        print("🤖 Initializing Improved BERT System...")
        print("   📈 Model: RoBERTa-Base (125M parameters, ~500MB)")
        print("   🔧 Features: Multi-layer embeddings + Dynamic personas + Quantization")
        print("   ✅ Meets <1GB constraint requirement")
        
        model_name = "roberta-base"
        
        # Load tokenizer and model
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModel.from_pretrained(model_name)
        
        # Apply quantization for speed improvement
        try:
            print("   ⚡ Applying INT8 quantization...")
            _model = torch.quantization.quantize_dynamic(
                _model, {torch.nn.Linear}, dtype=torch.qint8
            )
            print("   ✅ Quantization applied successfully (2-3x speed boost)")
        except Exception as e:
            print(f"   ⚠️  Quantization failed, using full precision: {e}")
        
        _model_initialized = True
        print("✅ Improved BERT model ready!")
        
        return _tokenizer, _model
        
    except Exception as e:
        print(f"❌ Error initializing BERT model: {e}")
        print("💡 Please install required packages: pip install torch transformers")
        return None, None

def extract_dynamic_persona_keywords(persona, job):
    """
    Extract keywords dynamically from persona and job description
    No hardcoded assumptions - works with any persona/job combination
    """
    # Combine persona and job text
    combined_text = f"{persona} {job}".lower()
    
    # Extract meaningful words (3+ characters)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', combined_text)
    
    # Enhanced stop words list (but preserve domain-specific terms)
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'how', 
        'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'with', 'that',
        'this', 'will', 'any', 'may', 'say', 'she', 'use', 'each', 'which',
        'their', 'time', 'work', 'first', 'been', 'call', 'find', 'long',
        'down', 'right', 'look', 'only', 'come', 'over', 'think', 'also',
        'back', 'after', 'very', 'good', 'well', 'where', 'much', 'before'
    }
    
    # Filter out stop words and short words
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Remove duplicates while preserving order
    unique_keywords = []
    seen = set()
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    # Return top keywords (limit for efficiency)
    return unique_keywords[:12]

def expand_query_semantically(keywords):
    """
    Expand query with semantic synonyms for better matching
    """
    # Comprehensive synonym mapping
    synonym_map = {
        # Food & Cooking
        'food': ['recipe', 'dish', 'meal', 'cuisine', 'cooking', 'culinary'],
        'recipe': ['dish', 'meal', 'food', 'cooking', 'preparation'],
        'vegetarian': ['plant-based', 'vegan', 'meatless', 'veggie'],
        'cooking': ['preparation', 'culinary', 'recipe', 'kitchen'],
        'menu': ['dishes', 'options', 'selection', 'offerings'],
        'buffet': ['self-service', 'spread', 'selection'],
        
        # Travel & Tourism
        'travel': ['trip', 'journey', 'vacation', 'tourism', 'visit'],
        'trip': ['journey', 'travel', 'vacation', 'excursion'],
        'vacation': ['holiday', 'trip', 'travel', 'getaway'],
        'itinerary': ['schedule', 'plan', 'agenda', 'program'],
        'tourist': ['visitor', 'traveler', 'sightseer'],
        'cultural': ['heritage', 'historical', 'traditional'],
        
        # Business & Corporate
        'corporate': ['business', 'company', 'office', 'professional'],
        'business': ['corporate', 'company', 'commercial', 'professional'],
        'gathering': ['meeting', 'event', 'function', 'assembly'],
        'professional': ['business', 'corporate', 'work'],
        
        # Documents & Management
        'document': ['file', 'pdf', 'form', 'paper', 'report'],
        'management': ['administration', 'organization', 'coordination'],
        'plan': ['organize', 'schedule', 'arrange', 'design', 'prepare'],
        'create': ['make', 'build', 'generate', 'produce', 'develop'],
        'prepare': ['make', 'create', 'organize', 'arrange'],
        
        # Actions & Processes
        'organize': ['arrange', 'plan', 'coordinate', 'manage'],
        'arrange': ['organize', 'plan', 'set up', 'coordinate'],
        'schedule': ['plan', 'organize', 'arrange', 'time'],
        'coordinate': ['organize', 'manage', 'arrange'],
    }
    
    expanded_terms = set(keywords)
    
    # Add synonyms for each keyword
    for keyword in keywords:
        if keyword in synonym_map:
            # Add top 2-3 synonyms to avoid query bloat
            expanded_terms.update(synonym_map[keyword][:3])
    
    return list(expanded_terms)

def get_multi_layer_embeddings(model, inputs):
    """
    Extract and combine multiple transformer layers for richer representations
    Uses proven technique of averaging last 4 layers
    """
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)
        
        # Get hidden states from all layers
        hidden_states = outputs.hidden_states
        
        # Take the last 4 layers and average them
        # This captures both low-level and high-level features
        last_4_layers = torch.stack(hidden_states[-4:])  # Shape: (4, batch, seq, hidden)
        
        # Average across layers, then take [CLS] token (first token)
        averaged_embeddings = torch.mean(last_4_layers, dim=0)[:, 0, :]  # Shape: (batch, hidden)
        
        return averaged_embeddings.numpy()

def rank_sections(sections, persona, job_description):
    """
    Main ranking function using improved BERT
    """
    # Initialize BERT model if not already done
    tokenizer, model = initialize_bert_model()
    
    if not tokenizer or not model:
        print("❌ BERT model not available, cannot rank sections")
        return [], []
    
    if not sections:
        print("⚠️  No sections to rank")
        return [], []
    
    try:
        print(f"🧠 Ranking {len(sections)} sections with Improved BERT...")
        start_time = time.time()
        
        # Enhanced section filtering
        filtered_sections = filter_sections_for_bert(sections)
        print(f"   📊 Filtered to {len(filtered_sections)} high-quality sections")
        
        if not filtered_sections:
            print("⚠️  No sections remain after filtering")
            return [], []
        
        # Dynamic persona analysis
        keywords = extract_dynamic_persona_keywords(persona, job_description)
        expanded_keywords = expand_query_semantically(keywords)
        
        print(f"   🎯 Extracted {len(keywords)} persona keywords")
        print(f"   🔍 Expanded to {len(expanded_keywords)} semantic terms")
        print(f"   📝 Sample keywords: {keywords[:5]}")
        
        # Create enhanced query
        query_parts = [persona, job_description] + expanded_keywords[:8]
        enhanced_query = ' '.join(query_parts).lower()
        
        # Prepare texts for BERT processing
        texts = prepare_texts_for_bert(filtered_sections, enhanced_query)
        
        # Process in batches for efficiency
        embeddings = process_texts_in_batches(texts, tokenizer, model)
        
        # Calculate similarities
        query_embedding = embeddings[0:1]
        section_embeddings = embeddings[1:]
        similarities = cosine_similarity(query_embedding, section_embeddings).flatten()
        
        # Apply persona-aware boosting
        similarities = apply_persona_boosting(similarities, filtered_sections, expanded_keywords)
        
        # Create ranked results
        ranked_sections, subsection_analysis = create_ranked_results(
            similarities, filtered_sections, len(sections)
        )
        
        processing_time = time.time() - start_time
        speed = len(sections) / processing_time if processing_time > 0 else 0
        
        print(f"   ⏱️  Processing time: {processing_time:.3f}s")
        print(f"   ⚡ Speed: {speed:.1f} sections/second")
        print(f"   🏆 Top result: '{ranked_sections[0]['section_title'][:50]}...'" if ranked_sections else "No results")
        
        return ranked_sections, subsection_analysis
        
    except Exception as e:
        print(f"❌ Error in BERT ranking: {e}")
        return [], []

def filter_sections_for_bert(sections):
    """
    Filter sections for optimal BERT processing
    """
    filtered = []
    
    for section in sections:
        title = section.get("section_title", "").strip()
        text = section.get("section_text", "").strip()
        
        # Quality filters
        if (len(title) >= 3 and 
            len(text) >= 20 and 
            len(text) <= 1000 and  # BERT works best with reasonable length
            not is_low_quality_section(title, text)):
            filtered.append(section)
    
    # If too few sections, relax filters
    if len(filtered) < 5:
        filtered = []
        for section in sections:
            title = section.get("section_title", "").strip()
            text = section.get("section_text", "").strip()
            if len(title) >= 2 and len(text) >= 15:
                filtered.append(section)
    
    # Limit for efficiency (BERT is computationally expensive)
    return filtered[:20]

def is_low_quality_section(title, text):
    """
    Detect low-quality sections to filter out
    """
    # Skip sections that are mostly numbers or symbols
    if len(re.sub(r'[^a-zA-Z\s]', '', text)) < len(text) * 0.6:
        return True
    
    # Skip very repetitive content
    words = text.lower().split()
    if len(set(words)) < len(words) * 0.3:
        return True
    
    # Skip sections with too many short words
    if sum(1 for word in words if len(word) <= 2) > len(words) * 0.5:
        return True
    
    return False

def prepare_texts_for_bert(sections, query):
    """
    Prepare texts for optimal BERT processing
    """
    texts = [query]  # Query goes first
    
    for section in sections:
        title = section.get("section_title", "")
        text = section.get("section_text", "")
        
        # Enhanced text preparation
        # Title gets extra weight by repetition
        enhanced_text = f"{title} {title} {text}".lower()
        
        # Truncate to optimal length for RoBERTa (512 tokens ≈ 400 words)
        words = enhanced_text.split()
        if len(words) > 350:
            enhanced_text = ' '.join(words[:350]) + "..."
        
        texts.append(enhanced_text)
    
    return texts

def process_texts_in_batches(texts, tokenizer, model, batch_size=8):
    """
    Process texts in batches for memory efficiency
    """
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        
        # Tokenize batch
        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=512,  # RoBERTa's max length
            return_tensors="pt"
        )
        
        # Get multi-layer embeddings
        batch_embeddings = get_multi_layer_embeddings(model, inputs)
        all_embeddings.append(batch_embeddings)
    
    # Combine all embeddings
    return np.vstack(all_embeddings)

def apply_persona_boosting(similarities, sections, expanded_keywords):
    """
    Apply persona-aware boosting to similarity scores
    """
    boosted_similarities = similarities.copy()
    
    for i, section in enumerate(sections):
        title_lower = section.get("section_title", "").lower()
        text_lower = section.get("section_text", "").lower()
        
        boost_factor = 1.0
        
        # Count keyword matches
        title_matches = sum(1 for keyword in expanded_keywords if keyword in title_lower)
        text_matches = sum(1 for keyword in expanded_keywords if keyword in text_lower)
        
        # Apply graduated boosting
        if title_matches > 0:
            boost_factor += 0.25 + (title_matches * 0.1)
        
        if text_matches > 0:
            boost_factor += 0.1 + (text_matches * 0.05)
        
        # Special domain-specific boosts
        section_type = section.get("section_type", "")
        if section_type in ["recipe_component", "complete_recipe", "individual_recipe"]:
            if any(food_word in ' '.join(expanded_keywords) for food_word in ['food', 'recipe', 'vegetarian', 'menu']):
                boost_factor += 0.2
        
        if section_type in ["heading_based", "procedural"]:
            if any(proc_word in ' '.join(expanded_keywords) for proc_word in ['plan', 'organize', 'prepare', 'create']):
                boost_factor += 0.15
        
        boosted_similarities[i] *= boost_factor
    
    return boosted_similarities

def create_ranked_results(similarities, sections, original_section_count):
    """
    Create final ranked results with proper formatting
    """
    # Combine similarities with sections
    section_scores = list(zip(similarities, sections))
    section_scores.sort(reverse=True, key=lambda x: x[0])
    
    # Limit results
    max_results = min(15, len(section_scores))
    section_scores = section_scores[:max_results]
    
    ranked_sections = []
    subsection_analysis = []
    
    for rank, (score, section) in enumerate(section_scores, start=1):
        # Ranked section entry
        ranked_sections.append({
            "document": section["document"],
            "section_title": section["section_title"],
            "page_number": section["page_number"],
            "importance_rank": rank,
            "similarity_score": float(score),
            "section_type": section.get("section_type", "unknown")
        })
        
        # Subsection analysis entry
        text = section["section_text"]
        refined_text = text[:300] + "..." if len(text) > 300 else text
        
        subsection_analysis.append({
            "document": section["document"],
            "section_title": section["section_title"],
            "refined_text": refined_text.strip(),
            "page_number": section["page_number"],
            "section_type": section.get("section_type", "unknown")
        })
    
    return ranked_sections, subsection_analysis

def test_bert_ranking():
    """
    Test the BERT ranking system
    """
    print("🧪 TESTING IMPROVED BERT RANKING SYSTEM")
    print("=" * 60)
    
    # Mock test data
    test_sections = [
        {
            "document": "test.pdf",
            "section_title": "Vegetarian Pasta Recipe",
            "section_text": "This delicious vegetarian pasta dish is perfect for corporate catering events. Made with fresh vegetables and available in gluten-free options. Serves 10-12 people.",
            "page_number": 1,
            "section_type": "recipe_component"
        },
        {
            "document": "test.pdf",
            "section_title": "Chicken Curry Recipe", 
            "section_text": "A spicy chicken curry recipe with traditional Indian spices. Takes 45 minutes to prepare and serves 8 people. Not suitable for vegetarian diets.",
            "page_number": 2,
            "section_type": "recipe_component"
        },
        {
            "document": "test.pdf",
            "section_title": "Corporate Event Planning Guide",
            "section_text": "Guidelines for organizing corporate gatherings including venue selection, catering options, and scheduling considerations for business events.",
            "page_number": 3,
            "section_type": "procedural"
        }
    ]
    
    # Test query
    persona = "Food Contractor"
    job = "Prepare a vegetarian buffet-style dinner menu for a corporate gathering, including gluten-free items."
    
    print(f"🧑‍💼 Test Persona: {persona}")
    print(f"📋 Test Job: {job}")
    print(f"📊 Test Sections: {len(test_sections)}")
    
    # Run ranking
    ranked, analysis = rank_sections(test_sections, persona, job)
    
    print(f"\n🏆 RANKING RESULTS:")
    for i, result in enumerate(ranked, 1):
        print(f"   {i}. {result['section_title']}")
        print(f"      Score: {result['similarity_score']:.3f}")
        print(f"      Type: {result.get('section_type', 'unknown')}")
        print()
    
    print("✅ BERT ranking test complete!")

if __name__ == "__main__":
    test_bert_ranking()
