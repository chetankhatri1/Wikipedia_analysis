#!/usr/bin/env python3
"""
Wikipedia Category Word Frequency Analyzer

This script takes a Wikipedia category as a command-line argument and outputs
the cumulative frequency of non-common words across all pages in that category.
It uses the MediaWiki API to fetch the data.
"""

import argparse
import requests
import re
import ssl
import os
import hashlib
from collections import Counter
import string
import sys
import time
from datetime import datetime
import pickle

# Try to import NLTK, but provide fallbacks if it's not available or has SSL issues
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("NLTK not available. Using basic tokenization and default stopwords.")

def download_nltk_resources():
    """Download required NLTK resources if not already present."""
    if not NLTK_AVAILABLE:
        return False
        
    try:
        # Try to find the resources
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            return True
        except LookupError:
            # Create a default SSL context that doesn't verify certificates
            # This is only for downloading NLTK resources and is not ideal for security
            # but helps bypass SSL certificate issues
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context
            
            print("Downloading required NLTK resources...")
            nltk.download('punkt')
            nltk.download('stopwords')
            return True
    except Exception as e:
        print(f"Error downloading NLTK resources: {e}")
        return False

# Default English stopwords list as fallback
DEFAULT_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
    'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them',
    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll",
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
    'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
    'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've",
    'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't",
    'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan',
    "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't",
    'wouldn', "wouldn't", 'also', 'one', 'two', 'three', 'first', 'second', 'third', 'may',
    'many', 'much', 'however', 'although', 'despite', 'like', 'unlike', 'whether', 'either',
    'neither', 'rather', 'instead'
}

def simple_tokenize(text):
    """Simple word tokenization function as fallback when NLTK is not available."""
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Split on whitespace
    return text.lower().split()

def get_pages_in_category(category, continue_param=None):
    """
    Get all pages in a Wikipedia category using the MediaWiki API.
    
    Args:
        category (str): The Wikipedia category name (without the 'Category:' prefix)
        continue_param (dict): Continuation parameters for pagination
        
    Returns:
        tuple: (list of page titles, continuation parameters for next request)
    """
    base_url = "https://en.wikipedia.org/w/api.php"
    
    # Add 'Category:' prefix if not present
    if not category.startswith("Category:"):
        category = f"Category:{category}"
    
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": 500,  # Maximum allowed by the API
        "cmtype": "page"  # Only get pages, not subcategories
    }
    
    # Add continuation parameters if provided
    if continue_param:
        params.update(continue_param)
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        
        # Extract page titles
        pages = [page["title"] for page in data.get("query", {}).get("categorymembers", [])]
        
        # Get continuation parameters if available
        continue_params = data.get("continue", None)
        
        return pages, continue_params
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching pages in category: {e}", file=sys.stderr)
        return [], None

def get_all_pages_in_category(category):
    """
    Get all pages in a category, handling pagination.
    
    Args:
        category (str): The Wikipedia category name
        
    Returns:
        list: All page titles in the category
    """
    all_pages = []
    continue_param = None
    
    print(f"Fetching pages in category '{category}'...")
    
    while True:
        pages, continue_param = get_pages_in_category(category, continue_param)
        all_pages.extend(pages)
        
        if not continue_param:
            break
        
        # Be nice to the API servers
        time.sleep(1)
    
    print(f"Found {len(all_pages)} pages in category '{category}'")
    return all_pages

def get_page_content(page_title):
    """
    Get the text content of a Wikipedia page.
    
    Args:
        page_title (str): The title of the Wikipedia page
        
    Returns:
        str: The text content of the page
    """
    base_url = "https://en.wikipedia.org/w/api.php"
    
    params = {
        "action": "query",
        "format": "json",
        "titles": page_title,
        "prop": "extracts",
        "explaintext": True,  # Get plain text instead of HTML
        "exsectionformat": "plain"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract the page content
        pages = data.get("query", {}).get("pages", {})
        
        # The API returns a dict with page IDs as keys
        for page_id in pages:
            return pages[page_id].get("extract", "")
        
        return ""
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching content for page '{page_title}': {e}", file=sys.stderr)
        return ""

def preprocess_text(text):
    """
    Preprocess text by removing punctuation, numbers, and converting to lowercase.
    
    Args:
        text (str): The input text
        
    Returns:
        str: The preprocessed text
    """
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    
    # Convert to lowercase
    text = text.lower()
    
    return text

def get_word_frequencies(text, stop_words):
    """
    Get the frequency of non-common words in a text.
    
    Args:
        text (str): The input text
        stop_words (set): Set of common words to exclude
        
    Returns:
        Counter: Word frequency counter
    """
    # Preprocess the text
    processed_text = preprocess_text(text)
    
    # Tokenize the text
    if NLTK_AVAILABLE:
        try:
            tokens = word_tokenize(processed_text)
        except Exception as e:
            print(f"Error tokenizing with NLTK: {e}. Falling back to simple tokenization.")
            tokens = simple_tokenize(processed_text)
    else:
        tokens = simple_tokenize(processed_text)
    
    # Remove stop words and short words (likely not meaningful)
    filtered_tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    
    # Count word frequencies
    word_freq = Counter(filtered_tokens)
    
    return word_freq

def get_cache_directory():
    """
    Get or create the cache directory for storing results.
    
    Returns:
        str: Path to the cache directory
    """
    # Create a cache directory in the script's directory
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
    
    # Create the directory if it doesn't exist
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    return cache_dir

def get_cache_filename(category):
    """
    Generate a cache filename for a category.
    
    Args:
        category (str): The Wikipedia category name
        
    Returns:
        str: Cache filename
    """
    # Create a hash of the category name to use as the filename
    category_hash = hashlib.md5(category.encode('utf-8')).hexdigest()
    return os.path.join(get_cache_directory(), f"{category_hash}.pickle")

def save_to_cache(category, word_frequencies, metadata=None):
    """
    Save word frequencies to cache.
    
    Args:
        category (str): The Wikipedia category name
        word_frequencies (Counter): Word frequency counter
        metadata (dict, optional): Additional metadata to store
    """
    cache_file = get_cache_filename(category)
    
    # Default metadata
    if metadata is None:
        metadata = {}
    
    # Add timestamp and category name to metadata
    metadata.update({
        'category': category,
        'timestamp': datetime.now().isoformat(),
        'word_count': sum(word_frequencies.values()),
        'unique_words': len(word_frequencies)
    })
    
    # Create the cache data structure
    cache_data = {
        'metadata': metadata,
        'word_frequencies': word_frequencies
    }
    
    # Save to file
    with open(cache_file, 'wb') as f:
        pickle.dump(cache_data, f)
    
    print(f"Results cached to {cache_file}")

def load_from_cache(category):
    """
    Load word frequencies from cache if available.
    
    Args:
        category (str): The Wikipedia category name
        
    Returns:
        tuple: (word_frequencies, metadata) if cache exists, else (None, None)
    """
    cache_file = get_cache_filename(category)
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Extract data from cache
            word_frequencies = cache_data.get('word_frequencies', Counter())
            metadata = cache_data.get('metadata', {})
            
            # Print cache information
            timestamp = metadata.get('timestamp', 'unknown')
            if timestamp != 'unknown':
                # Convert ISO format string to datetime object
                cache_date = datetime.fromisoformat(timestamp)
                cache_age = datetime.now() - cache_date
                print(f"Using cached results from {cache_date.strftime('%Y-%m-%d %H:%M:%S')} ({cache_age.days} days, {cache_age.seconds // 3600} hours ago)")
            else:
                print("Using cached results (timestamp unknown)")
            
            return word_frequencies, metadata
        except Exception as e:
            print(f"Error loading cache: {e}. Will reprocess category.")
    
    return None, None

def analyze_category(category, top_n=100, force_refresh=False):
    """
    Analyze word frequencies across all pages in a Wikipedia category.
    
    Args:
        category (str): The Wikipedia category name
        top_n (int): Number of top frequent words to display
        force_refresh (bool): If True, ignore cache and reprocess category
        
    Returns:
        Counter: Combined word frequency counter
    """
    # Check cache first unless force_refresh is True
    if not force_refresh:
        word_frequencies, metadata = load_from_cache(category)
        if word_frequencies is not None:
            return word_frequencies
    
    # If we're here, we need to process the category
    print(f"Processing category '{category}'" + (" (forced refresh)" if force_refresh else ""))
    
    # Try to download NLTK resources if needed
    nltk_available = download_nltk_resources()
    
    # Get stop words (common words)
    if nltk_available:
        try:
            stop_words = set(stopwords.words('english'))
        except Exception as e:
            print(f"Error loading NLTK stopwords: {e}. Using default stopwords list.")
            stop_words = DEFAULT_STOPWORDS
    else:
        stop_words = DEFAULT_STOPWORDS
    
    print(f"Using a list of {len(stop_words)} stopwords for filtering.")
    
    # Get all pages in the category
    pages = get_all_pages_in_category(category)
    
    if not pages:
        print(f"No pages found in category '{category}'")
        return Counter()
    
    # Initialize a counter for all words
    all_word_freq = Counter()
    
    # Process each page
    for i, page_title in enumerate(pages):
        print(f"Processing page {i+1}/{len(pages)}: {page_title}")
        
        # Get page content
        content = get_page_content(page_title)
        
        if not content:
            print(f"  No content found for page '{page_title}'")
            continue
        
        # Get word frequencies for this page
        word_freq = get_word_frequencies(content, stop_words)
        
        # Update the overall counter
        all_word_freq.update(word_freq)
        
        # Be nice to the API servers
        time.sleep(1)
    
    # Save results to cache
    save_to_cache(category, all_word_freq)
    
    return all_word_freq

def list_cached_categories():
    """
    List all categories that have been cached.
    
    Returns:
        list: List of tuples (category_name, timestamp, word_count, unique_words)
    """
    cache_dir = get_cache_directory()
    cached_data = []
    
    if not os.path.exists(cache_dir):
        return cached_data
    
    for filename in os.listdir(cache_dir):
        if filename.endswith('.pickle'):
            try:
                filepath = os.path.join(cache_dir, filename)
                with open(filepath, 'rb') as f:
                    cache_data = pickle.load(f)
                
                metadata = cache_data.get('metadata', {})
                category = metadata.get('category', 'Unknown')
                timestamp = metadata.get('timestamp', 'Unknown')
                word_count = metadata.get('word_count', 0)
                unique_words = metadata.get('unique_words', 0)
                
                cached_data.append((category, timestamp, word_count, unique_words))
            except Exception as e:
                print(f"Error reading cache file {filename}: {e}")
    
    return cached_data

def main():
    """Main function to parse arguments and run the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze word frequencies in Wikipedia categories"
    )
    parser.add_argument(
        "category", 
        nargs='?',
        help="Wikipedia category to analyze (e.g., 'Large_language_models')"
    )
    parser.add_argument(
        "-n", "--top", 
        type=int, 
        default=100, 
        help="Number of top frequent words to display (default: 100)"
    )
    parser.add_argument(
        "-f", "--force", 
        action="store_true", 
        help="Force refresh of category data even if cached"
    )
    parser.add_argument(
        "-l", "--list-cache", 
        action="store_true", 
        help="List all cached categories"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Save results to a text file"
    )
    
    args = parser.parse_args()
    
    # List cached categories if requested
    if args.list_cache:
        cached_data = list_cached_categories()
        if not cached_data:
            print("No cached categories found.")
            return
        
        print("\nCached Categories:")
        print("=" * 80)
        print(f"{'Category':<30} {'Timestamp':<25} {'Total Words':<15} {'Unique Words':<15}")
        print("-" * 80)
        
        for category, timestamp, word_count, unique_words in sorted(cached_data):
            # Format the timestamp if it's a valid ISO format
            try:
                if timestamp != 'Unknown':
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
            
            print(f"{category:<30} {timestamp:<25} {word_count:<15} {unique_words:<15}")
        
        return
    
    # Ensure a category is provided if not listing cache
    if not args.category:
        parser.error("a category must be provided unless --list-cache is used")
    
    # Analyze the category
    word_frequencies = analyze_category(args.category, args.top, args.force)
    
    if not word_frequencies:
        return
    
    # Prepare the results
    results = ["\nTop non-common words in category:"]
    results.append("=" * 40)
    results.append(f"{'Word':<20} {'Frequency':<10}")
    results.append("-" * 40)
    
    for word, freq in word_frequencies.most_common(args.top):
        results.append(f"{word:<20} {freq:<10}")
    
    # Display the results
    for line in results:
        print(line)
    
    # Save to file if requested
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(f"Word frequency analysis for Wikipedia category: {args.category}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write('\n'.join(results))
            print(f"\nResults saved to {args.output}")
        except Exception as e:
            print(f"Error saving results to file: {e}")

if __name__ == "__main__":
    main()
