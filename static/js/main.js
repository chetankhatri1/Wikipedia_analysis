/**
 * Wikipedia Category Word Cloud Visualizer
 * Main JavaScript file for handling user interactions and API calls
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const categoryForm = document.getElementById('category-form');
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    const loadingIndicator = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const wordcloudImg = document.getElementById('wordcloud-img');
    const categoryName = document.getElementById('category-name');
    const totalWords = document.getElementById('total-words');
    const uniqueWords = document.getElementById('unique-words');
    const wordTableBody = document.getElementById('word-table-body');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const cachedCategories = document.querySelectorAll('.cached-category');
    const colorPaletteSelect = document.getElementById('color_palette');
    const colorPreview = document.getElementById('color-preview');

    // Event Listeners
    categoryForm.addEventListener('submit', handleFormSubmit);
    
    // Add click event to cached categories
    cachedCategories.forEach(item => {
        item.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            document.getElementById('category').value = category;
            loadCachedCategory(category);
        });
    });
    
    // Initialize color palette preview
    if (colorPaletteSelect) {
        updateColorPreview();
        colorPaletteSelect.addEventListener('change', updateColorPreview);
    }

    // Tab switching functionality
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Update active tab content
            tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    /**
     * Handle form submission for category analysis
     * @param {Event} e - Form submit event
     */
    function handleFormSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(categoryForm);
        const category = formData.get('category').trim();
        
        if (!category) {
            showError('Please enter a Wikipedia category name');
            return;
        }
        
        // Show loading indicator
        showLoading();
        
        // Prepare form data for submission
        const data = new FormData();
        data.append('category', category);
        data.append('top_n', formData.get('top_n'));
        data.append('force_refresh', formData.get('force_refresh') ? 'true' : 'false');
        
        // Send request to server
        fetch('/analyze', {
            method: 'POST',
            body: data
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to analyze category');
                });
            }
            return response.json();
        })
        .then(data => {
            displayResults(data);
        })
        .catch(error => {
            showError(error.message);
        });
    }

    /**
     * Load data for a cached category
     * @param {string} category - The category name to load
     */
    function loadCachedCategory(category) {
        showLoading();
        
        const topN = document.getElementById('top_n').value;
        const colorPalette = document.getElementById('color_palette').value;
        
        fetch(`/load_cached/${encodeURIComponent(category)}?top_n=${topN}&color_palette=${colorPalette}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Failed to load cached category');
                    });
                }
                return response.json();
            })
            .then(data => {
                displayResults(data);
            })
            .catch(error => {
                showError(error.message);
            });
    }

    /**
     * Display the analysis results
     * @param {Object} data - The analysis results data
     */
    function displayResults(data) {
        // Hide loading indicator
        hideLoading();
        
        // Update category name
        categoryName.textContent = data.category;
        
        // Update word cloud image
        wordcloudImg.src = `data:image/png;base64,${data.wordcloud}`;
        
        // Update statistics
        totalWords.textContent = data.total_words.toLocaleString();
        uniqueWords.textContent = data.unique_words.toLocaleString();
        
        // Update word frequency table
        wordTableBody.innerHTML = '';
        data.table_data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.word}</td>
                <td>${item.frequency.toLocaleString()}</td>
            `;
            wordTableBody.appendChild(row);
        });
        
        // Display used colors if available
        if (data.palette_colors && data.palette_colors.length > 0) {
            // Check if the colors display already exists, if not create it
            let usedColorsEl = document.querySelector('.used-colors');
            if (!usedColorsEl) {
                usedColorsEl = document.createElement('div');
                usedColorsEl.className = 'used-colors';
                
                const label = document.createElement('div');
                label.className = 'used-colors-label';
                label.textContent = 'Colors Used:';
                
                const swatches = document.createElement('div');
                swatches.className = 'used-colors-swatches';
                
                usedColorsEl.appendChild(label);
                usedColorsEl.appendChild(swatches);
                
                // Insert after the wordcloud title
                const wordcloudTab = document.getElementById('wordcloud-tab');
                wordcloudTab.insertBefore(usedColorsEl, wordcloudTab.firstChild);
            }
            
            // Update the swatches
            const swatchesContainer = usedColorsEl.querySelector('.used-colors-swatches');
            swatchesContainer.innerHTML = '';
            
            data.palette_colors.forEach(color => {
                const swatch = document.createElement('div');
                swatch.className = 'used-color-swatch';
                swatch.style.backgroundColor = color;
                swatchesContainer.appendChild(swatch);
            });
        }
        
        // Show results content
        resultsContent.classList.remove('hidden');
        
        // Reset to word cloud tab
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabButtons[0].classList.add('active');
        tabPanes.forEach(pane => pane.classList.remove('active'));
        document.getElementById('wordcloud-tab').classList.add('active');
    }

    /**
     * Show loading indicator and hide other content
     */
    function showLoading() {
        loadingIndicator.classList.remove('hidden');
        resultsContent.classList.add('hidden');
        errorMessage.classList.add('hidden');
    }

    /**
     * Hide loading indicator
     */
    function hideLoading() {
        loadingIndicator.classList.add('hidden');
    }

    /**
     * Show error message
     * @param {string} message - The error message to display
     */
    function showError(message) {
        hideLoading();
        resultsContent.classList.add('hidden');
        errorMessage.classList.remove('hidden');
        errorText.textContent = message;
    }
    
    /**
     * Update the color preview based on the selected palette
     */
    function updateColorPreview() {
        if (!colorPaletteSelect || !colorPreview) return;
        
        // Get the selected option
        const selectedOption = colorPaletteSelect.options[colorPaletteSelect.selectedIndex];
        
        // Get the colors from the data attribute
        let colors = [];
        try {
            colors = JSON.parse(selectedOption.getAttribute('data-colors'));
        } catch (e) {
            console.error('Error parsing colors:', e);
        }
        
        // Clear the preview
        colorPreview.innerHTML = '';
        
        // Add color swatches
        colors.forEach(color => {
            const swatch = document.createElement('div');
            swatch.className = 'color-swatch';
            swatch.style.backgroundColor = color;
            colorPreview.appendChild(swatch);
        });
    }
});
