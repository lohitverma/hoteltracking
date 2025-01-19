class LocationSearch {
    constructor() {
        this.selectedLocation = null;
        this.searchResults = [];
        this.init();
    }

    async init() {
        // Create location search UI
        const searchContainer = document.createElement('div');
        searchContainer.className = 'location-search relative w-full mb-4';
        searchContainer.innerHTML = `
            <label class="block text-sm font-medium text-gray-700 mb-1">
                Destination
            </label>
            <div class="relative">
                <input
                    type="text"
                    id="locationInput"
                    class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Search for a city..."
                    autocomplete="off"
                >
                <div id="locationResults" class="absolute z-10 w-full mt-1 bg-white rounded-lg shadow-lg hidden">
                    <div id="popularDestinations" class="p-2 border-b">
                        <h3 class="text-sm font-semibold text-gray-600 mb-2">Popular Destinations</h3>
                        <div id="popularList" class="grid grid-cols-2 gap-2"></div>
                    </div>
                    <div id="searchResults" class="max-h-60 overflow-y-auto"></div>
                </div>
            </div>
        `;

        // Add to the search form
        const searchForm = document.querySelector('#searchForm');
        searchForm.insertBefore(searchContainer, searchForm.firstChild);

        // Initialize event listeners
        this.initEventListeners();
        
        // Load popular destinations
        await this.loadPopularDestinations();
    }

    async initEventListeners() {
        const input = document.getElementById('locationInput');
        const results = document.getElementById('locationResults');

        // Show results when input is focused
        input.addEventListener('focus', () => {
            results.classList.remove('hidden');
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!results.contains(e.target) && e.target !== input) {
                results.classList.add('hidden');
            }
        });

        // Handle input changes
        let debounceTimer;
        input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => this.handleSearch(e.target.value), 300);
        });
    }

    async loadPopularDestinations() {
        try {
            const response = await fetch('/api/locations/popular');
            const destinations = await response.json();
            
            const popularList = document.getElementById('popularList');
            popularList.innerHTML = destinations.map(dest => `
                <button
                    class="location-item p-2 text-left hover:bg-gray-100 rounded-lg transition-colors w-full"
                    data-id="${dest.id}"
                    data-name="${dest.name}, ${dest.country}"
                >
                    <div class="text-sm font-medium">${dest.name}</div>
                    <div class="text-xs text-gray-500">${dest.country}</div>
                </button>
            `).join('');

            // Add click handlers
            popularList.querySelectorAll('.location-item').forEach(item => {
                item.addEventListener('click', () => this.selectLocation(item));
            });
        } catch (error) {
            console.error('Error loading popular destinations:', error);
        }
    }

    async handleSearch(query) {
        if (!query) {
            document.getElementById('searchResults').innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/api/locations/search?query=${encodeURIComponent(query)}`);
            const locations = await response.json();
            this.searchResults = locations;

            const resultsContainer = document.getElementById('searchResults');
            resultsContainer.innerHTML = locations.map(location => `
                <button
                    class="location-item p-3 text-left hover:bg-gray-100 w-full transition-colors"
                    data-id="${location.id}"
                    data-name="${location.name}, ${location.country}"
                >
                    <div class="text-sm font-medium">${location.name}</div>
                    <div class="text-xs text-gray-500">
                        ${[location.city, location.state, location.country].filter(Boolean).join(', ')}
                    </div>
                </button>
            `).join('');

            // Add click handlers
            resultsContainer.querySelectorAll('.location-item').forEach(item => {
                item.addEventListener('click', () => this.selectLocation(item));
            });
        } catch (error) {
            console.error('Error searching locations:', error);
        }
    }

    selectLocation(element) {
        const id = element.dataset.id;
        const name = element.dataset.name;
        
        // Update input and store selection
        document.getElementById('locationInput').value = name;
        this.selectedLocation = { id, name };
        
        // Hide results
        document.getElementById('locationResults').classList.add('hidden');
        
        // Dispatch event for other components
        const event = new CustomEvent('locationSelected', {
            detail: this.selectedLocation
        });
        document.dispatchEvent(event);
    }

    getSelectedLocation() {
        return this.selectedLocation;
    }
}
