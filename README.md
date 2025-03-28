# Wikipedia Category Word Frequency Analyzer

This script analyzes Wikipedia categories to find the cumulative frequency of non-common words across all pages in a specified category. It includes a caching system to avoid reprocessing the same categories multiple times.

## Features

- Fetches all pages within a specified Wikipedia category using the MediaWiki API
- Removes common words (stopwords) and short words to focus on meaningful content
- Analyzes text content to calculate word frequencies
- Displays the most frequent non-common words in the category
- **Caches results locally** to avoid redundant processing of the same categories
- Exports results to text files for further analysis

## Requirements

- Python 3.6+
- Required packages: requests, nltk

## Installation

1. Clone this repository or download the files
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with a Wikipedia category name as an argument:

```bash
python wikipedia_category_analyzer.py "Large_language_models"
```

### Command-line Options

- `-n` or `--top`: Number of top frequent words to display (default: 100)
- `-f` or `--force`: Force refresh of category data even if cached
- `-l` or `--list-cache`: List all cached categories and their metadata
- `-o` or `--output`: Save results to a text file

### Examples

Analyze a category and display top 50 words:

```bash
python wikipedia_category_analyzer.py "Large_language_models" --top 50
```

Force reprocessing a category (ignore cache):

```bash
python wikipedia_category_analyzer.py "Large_language_models" --force
```

List all cached categories:

```bash
python wikipedia_category_analyzer.py --list-cache
```

Save results to a file:

```bash
python wikipedia_category_analyzer.py "Large_language_models" -o results.txt
```

## Caching System

The script automatically caches the results of each category analysis in a `cache` directory. This significantly speeds up subsequent analyses of the same category. The cache includes:

- Word frequency data
- Metadata (timestamp, category name, word count, etc.)

You can view all cached categories using the `--list-cache` option, and force a refresh of cached data using the `--force` option.

## Notes

- The script automatically downloads required NLTK resources on first run
- The analysis may take some time for large categories due to API rate limiting
- Category names are case-sensitive and should match Wikipedia's format
- You can use the category name with or without the "Category:" prefix
