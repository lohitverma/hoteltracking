// Initialize components
let locationSearch;
let selectedLocation = null;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize location search
    locationSearch = new LocationSearch();
    
    // Initialize date pickers
    flatpickr("#checkIn", {
        minDate: "today",
        onChange: function(selectedDates) {
            // Set minimum date for checkout
            const checkOut = document.getElementById("checkOut")._flatpickr;
            checkOut.set("minDate", selectedDates[0]);
        }
    });
    
    flatpickr("#checkOut", {
        minDate: "today"
    });
    
    // Handle location selection
    document.addEventListener('locationSelected', (e) => {
        selectedLocation = e.detail;
    });
    
    // Handle form submission
    document.getElementById('searchForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!selectedLocation) {
            showError('Please select a destination');
            return;
        }
        
        const checkIn = document.getElementById('checkIn').value;
        const checkOut = document.getElementById('checkOut').value;
        const guests = document.getElementById('guests').value;
        const rooms = document.getElementById('rooms').value;
        
        if (!checkIn || !checkOut) {
            showError('Please select check-in and check-out dates');
            return;
        }
        
        try {
            showLoading();
            
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    location_id: selectedLocation.id,
                    location_name: selectedLocation.name,
                    check_in: checkIn,
                    check_out: checkOut,
                    guests: parseInt(guests),
                    rooms: parseInt(rooms)
                })
            });
            
            if (!response.ok) {
                throw new Error('Search failed');
            }
            
            const hotels = await response.json();
            displayResults(hotels);
            
        } catch (error) {
            showError('Error searching hotels. Please try again.');
            console.error('Search error:', error);
        } finally {
            hideLoading();
        }
    });
});

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    setTimeout(() => {
        errorDiv.classList.add('hidden');
    }, 5000);
}

function showLoading() {
    document.getElementById('loadingSpinner').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loadingSpinner').classList.add('hidden');
}

function displayResults(hotels) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = '';
    resultsContainer.classList.remove('hidden');
    
    if (hotels.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-8">
                <p class="text-gray-500">No hotels found for your search criteria.</p>
            </div>
        `;
        return;
    }
    
    hotels.forEach(hotel => {
        const hotelCard = createHotelCard(hotel);
        resultsContainer.appendChild(hotelCard);
    });
}

function createHotelCard(hotel) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md overflow-hidden mb-4 hover:shadow-lg transition-shadow';
    
    card.innerHTML = `
        <div class="flex flex-col md:flex-row">
            <div class="md:w-1/3">
                <img src="${hotel.image_url}" alt="${hotel.name}" 
                    class="w-full h-48 md:h-full object-cover">
            </div>
            <div class="p-4 md:w-2/3">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="text-xl font-semibold mb-2">${hotel.name}</h3>
                        <p class="text-gray-600 mb-2">${hotel.location}</p>
                        ${hotel.rating ? `
                            <div class="flex items-center mb-2">
                                ${createStarRating(hotel.rating)}
                                <span class="ml-1 text-sm text-gray-600">${hotel.rating}/5</span>
                            </div>
                        ` : ''}
                    </div>
                    <div class="text-right">
                        <p class="text-2xl font-bold text-blue-600">
                            ${hotel.currency} ${hotel.price}
                        </p>
                        <p class="text-sm text-gray-500">per night</p>
                    </div>
                </div>
                
                <div class="mt-4 flex justify-between items-center">
                    <div>
                        ${hotel.provider ? `
                            <span class="text-sm text-gray-500">
                                Provided by ${hotel.provider}
                            </span>
                        ` : ''}
                    </div>
                    <button 
                        onclick="showHotelDetails('${hotel.hotel_id}')"
                        class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                    >
                        View Details
                    </button>
                </div>
            </div>
        </div>
    `;
    
    return card;
}

function createStarRating(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const stars = [];
    
    for (let i = 0; i < 5; i++) {
        if (i < fullStars) {
            stars.push('<i class="fas fa-star text-yellow-400"></i>');
        } else if (i === fullStars && hasHalfStar) {
            stars.push('<i class="fas fa-star-half-alt text-yellow-400"></i>');
        } else {
            stars.push('<i class="far fa-star text-yellow-400"></i>');
        }
    }
    
    return stars.join('');
}

async function showHotelDetails(hotelId) {
    try {
        const response = await fetch(`/api/hotel/${hotelId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch hotel details');
        }
        
        const hotel = await response.json();
        showHotelModal(hotel);
    } catch (error) {
        showError('Error loading hotel details');
        console.error('Error:', error);
    }
}

function showHotelModal(hotel) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50';
    
    modal.innerHTML = `
        <div class="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div class="p-6">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="text-2xl font-bold">${hotel.name}</h2>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    ${hotel.images.map(image => `
                        <img src="${image}" alt="${hotel.name}" class="w-full h-48 object-cover rounded">
                    `).join('')}
                </div>
                
                <p class="text-gray-700 mb-4">${hotel.description}</p>
                
                <div class="mb-4">
                    <h3 class="font-semibold mb-2">Amenities</h3>
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                        ${hotel.amenities.map(amenity => `
                            <div class="flex items-center">
                                <i class="fas fa-check text-green-500 mr-2"></i>
                                <span>${amenity}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="flex justify-end mt-6">
                    <button 
                        onclick="this.closest('.fixed').remove()"
                        class="bg-gray-500 text-white px-4 py-2 rounded mr-2 hover:bg-gray-600 transition-colors"
                    >
                        Close
                    </button>
                    <button 
                        onclick="createPriceAlert('${hotel.hotel_id}')"
                        class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                    >
                        Set Price Alert
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function PriceChart({ priceHistory }) {
    const chartRef = React.useRef(null);
    const [chart, setChart] = React.useState(null);

    React.useEffect(() => {
        if (chartRef.current && priceHistory) {
            if (chart) {
                chart.destroy();
            }

            const dates = priceHistory.map(item => item.date);
            const prices = priceHistory.map(item => item.price);

            const newChart = new Chart(chartRef.current, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Price History',
                        data: prices,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: '30-Day Price Trend',
                            font: {
                                size: 16,
                                family: 'Poppins'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
            setChart(newChart);
        }
        return () => {
            if (chart) {
                chart.destroy();
            }
        };
    }, [priceHistory]);

    return (
        <div className="chart-container">
            <canvas ref={chartRef}></canvas>
        </div>
    );
}

function HotelCard({ hotel, onViewDetails }) {
    const [showPriceHistory, setShowPriceHistory] = React.useState(false);

    const getPriceStats = () => {
        if (!hotel.price_history || hotel.price_history.length === 0) return null;
        
        const prices = hotel.price_history.map(h => h.price);
        const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
        const min = Math.min(...prices);
        const max = Math.max(...prices);
        
        return { avg: avg.toFixed(2), min: min.toFixed(2), max: max.toFixed(2) };
    };

    const stats = getPriceStats();

    return (
        <div className="hotel-card bg-white rounded-lg shadow-lg overflow-hidden">
            <img src={hotel.image_url} alt={hotel.name} className="hotel-image w-full" />
            <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                    <h2 className="text-xl font-semibold text-gray-800">{hotel.name}</h2>
                    <span className="price-tag">${hotel.price}</span>
                </div>
                <div className="text-gray-600 space-y-2">
                    <p className="flex items-center">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                        </svg>
                        {hotel.location}
                    </p>
                    <p className="flex items-center">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                        </svg>
                        {hotel.available_rooms} rooms available
                    </p>
                    <div className="flex items-center">
                        <svg className="w-5 h-5 mr-2 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                        </svg>
                        {hotel.rating} / 5.0
                    </div>
                </div>

                {stats && (
                    <div className="stats-container">
                        <div className="stat-card">
                            <div className="stat-value">${stats.min}</div>
                            <div className="text-sm text-gray-500">Lowest</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">${stats.avg}</div>
                            <div className="text-sm text-gray-500">Average</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">${stats.max}</div>
                            <div className="text-sm text-gray-500">Highest</div>
                        </div>
                    </div>
                )}

                <div className="mt-6 flex space-x-4">
                    <button
                        className="btn-primary flex-1"
                        onClick={() => setShowPriceHistory(!showPriceHistory)}
                    >
                        {showPriceHistory ? 'Hide Price History' : 'Show Price History'}
                    </button>
                    <button
                        className="btn-secondary flex-1"
                        onClick={() => onViewDetails(hotel.hotel_id)}
                    >
                        View Details
                    </button>
                </div>

                {showPriceHistory && hotel.price_history && (
                    <div className="mt-6">
                        <PriceChart priceHistory={hotel.price_history} />
                    </div>
                )}
            </div>
        </div>
    );
}

function App() {
    const [hotels, setHotels] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [searchParams, setSearchParams] = React.useState({
        location: '',
        check_in: '',
        check_out: '',
        guests: 2
    });

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchParams)
            });
            if (!response.ok) {
                throw new Error('Failed to fetch hotels');
            }
            const data = await response.json();
            setHotels(data);
        } catch (error) {
            setError(error.message);
            console.error('Error:', error);
        }
        setLoading(false);
    };

    const handleInputChange = (e) => {
        setSearchParams({
            ...searchParams,
            [e.target.name]: e.target.value
        });
    };

    const handleViewDetails = async (hotelId) => {
        try {
            const response = await fetch(`/api/hotel/${hotelId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch hotel details');
            }
            const data = await response.json();
            // Implement modal or navigation here
            console.log('Hotel details:', data);
        } catch (error) {
            console.error('Error fetching hotel details:', error);
        }
    };

    return (
        <div className="min-h-screen">
            <div className="hero-section text-white py-16 px-4">
                <div className="container mx-auto text-center">
                    <h1 className="text-5xl font-bold mb-4">Find Your Perfect Stay</h1>
                    <p className="text-xl mb-8">Track hotel prices and get the best deals for your next trip</p>
                    
                    <form onSubmit={handleSearch} className="search-form max-w-4xl mx-auto p-6">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <input
                                type="text"
                                name="location"
                                placeholder="Where are you going?"
                                value={searchParams.location}
                                onChange={handleInputChange}
                                className="p-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500 outline-none"
                                required
                            />
                            <input
                                type="date"
                                name="check_in"
                                value={searchParams.check_in}
                                onChange={handleInputChange}
                                className="p-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500 outline-none"
                                required
                            />
                            <input
                                type="date"
                                name="check_out"
                                value={searchParams.check_out}
                                onChange={handleInputChange}
                                className="p-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500 outline-none"
                                required
                            />
                            <button
                                type="submit"
                                className="bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition-colors"
                                disabled={loading}
                            >
                                {loading ? (
                                    <div className="flex items-center justify-center">
                                        <div className="loading-spinner mr-2"></div>
                                        Searching...
                                    </div>
                                ) : (
                                    'Search Hotels'
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <div className="container mx-auto px-4 py-12">
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6">
                        Error: {error}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {hotels.map(hotel => (
                        <HotelCard
                            key={hotel.hotel_id}
                            hotel={hotel}
                            onViewDetails={handleViewDetails}
                        />
                    ))}
                </div>

                {hotels.length === 0 && !loading && !error && (
                    <div className="text-center text-gray-500 mt-8">
                        <p className="text-xl">Start your search to find the best hotel deals!</p>
                    </div>
                )}
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));
