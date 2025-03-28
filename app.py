#!/usr/bin/env python3
"""
Wikipedia Category Word Cloud Visualizer

This Flask application provides a web interface for the Wikipedia Category Analyzer,
displaying word frequencies as an interactive word cloud.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from wordcloud import WordCloud
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

# Import color palettes
from colour_palette import get_all_color_palettes

# Import functions from the analyzer script
from wikipedia_category_analyzer import (
    analyze_category, 
    list_cached_categories, 
    load_from_cache, 
    get_cache_directory
)

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main page with the form and word cloud display area."""
    # Get list of cached categories for the dropdown
    cached_categories = list_cached_categories()
    
    # Get color palettes for the dropdown
    color_palettes = get_all_color_palettes()
    palette_options = [
        {"name": palette.__class__.__name__, "colors": palette.colors}
        for palette in color_palettes
    ]
    
    return render_template('index.html', cached_categories=cached_categories, palette_options=palette_options)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Process the category and generate word cloud data."""
    category = request.form.get('category', '')
    top_n = int(request.form.get('top_n', 100))
    force_refresh = request.form.get('force_refresh') == 'true'
    color_palette = request.form.get('color_palette', 'Tableau10')
    
    if not category:
        return jsonify({'error': 'Category name is required'}), 400
    
    try:
        # Use the analyzer function to get word frequencies
        word_frequencies = analyze_category(category, top_n=top_n, force_refresh=force_refresh)
        
        if not word_frequencies:
            return jsonify({'error': 'No word frequencies found for this category'}), 404
        
        # Get the selected color palette
        selected_palette = None
        for palette in get_all_color_palettes():
            if palette.__class__.__name__ == color_palette:
                selected_palette = palette
                break
        
        # Generate word cloud image
        wordcloud_base64 = generate_wordcloud(word_frequencies, selected_palette)
        
        # Prepare data for the table view
        table_data = [{'word': word, 'frequency': freq} 
                     for word, freq in word_frequencies.most_common(top_n)]
        
        return jsonify({
            'wordcloud': wordcloud_base64,
            'table_data': table_data,
            'category': category,
            'total_words': sum(word_frequencies.values()),
            'unique_words': len(word_frequencies),
            'color_palette': color_palette,
            'palette_colors': selected_palette.colors if selected_palette else []
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cached_data')
def cached_data():
    """Return a list of all cached categories."""
    try:
        categories = list_cached_categories()
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load_cached/<path:category>')
def load_cached(category):
    """Load word frequencies from cache for a specific category."""
    try:
        word_frequencies, metadata = load_from_cache(category)
        
        if not word_frequencies:
            return jsonify({'error': 'Category not found in cache'}), 404
        
        top_n = int(request.args.get('top_n', 100))
        color_palette = request.args.get('color_palette', 'Tableau10')
        
        # Get the selected color palette
        selected_palette = None
        for palette in get_all_color_palettes():
            if palette.__class__.__name__ == color_palette:
                selected_palette = palette
                break
        
        # Generate word cloud image
        wordcloud_base64 = generate_wordcloud(word_frequencies, selected_palette)
        
        # Prepare data for the table view
        table_data = [{'word': word, 'frequency': freq} 
                     for word, freq in word_frequencies.most_common(top_n)]
        
        return jsonify({
            'wordcloud': wordcloud_base64,
            'table_data': table_data,
            'category': category,
            'total_words': sum(word_frequencies.values()),
            'unique_words': len(word_frequencies),
            'metadata': metadata,
            'color_palette': color_palette,
            'palette_colors': selected_palette.colors if selected_palette else []
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_wordcloud(word_frequencies, color_palette=None):
    """Generate a word cloud image from word frequencies."""
    # Set up color function if a palette is provided
    colormap = None
    if color_palette:
        from matplotlib.colors import ListedColormap
        colormap = ListedColormap(color_palette.colors)
    
    # Create a WordCloud object
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white',
        max_words=100,
        contour_width=1,
        contour_color='steelblue',
        colormap=colormap
    ).generate_from_frequencies(word_frequencies)
    
    # Convert the image to a base64 string for embedding in HTML
    img = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode('utf-8')

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True)
