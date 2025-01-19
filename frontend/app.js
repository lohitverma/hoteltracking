// PriceChart Component
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
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Price Trends'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Price (USD)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
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
        <div className="bg-white p-4 rounded-lg shadow">
            <canvas ref={chartRef}></canvas>
        </div>
    );
}

// HotelCard Component
function HotelCard({ hotel, onViewDetails }) {
    const [showPriceHistory, setShowPriceHistory] = React.useState(false);

    const togglePriceHistory = () => {
        setShowPriceHistory(!showPriceHistory);
    };

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
        <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-2">{hotel.name}</h2>
            <div className="text-gray-600 mb-4">
                <p>Location: {hotel.location}</p>
                <p className="text-lg font-semibold text-green-600">
                    Current Price: ${hotel.price} {hotel.currency}
                </p>
                <p>Available Rooms: {hotel.available_rooms}</p>
                {hotel.rating && (
                    <p>Rating: {hotel.rating} ⭐</p>
                )}
                {stats && (
                    <div className="mt-2 text-sm">
                        <p>30-Day Price Range:</p>
                        <p>Min: ${stats.min} | Avg: ${stats.avg} | Max: ${stats.max}</p>
                    </div>
                )}
            </div>
            <div className="flex space-x-2">
                <button
                    className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                    onClick={togglePriceHistory}
                >
                    {showPriceHistory ? 'Hide Price History' : 'Show Price History'}
                </button>
                <button
                    className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    onClick={() => onViewDetails(hotel.hotel_id)}
                >
                    View Details
                </button>
            </div>
            {showPriceHistory && hotel.price_history && (
                <div className="mt-4">
                    <PriceChart priceHistory={hotel.price_history} />
                </div>
            )}
        </div>
    );
}

// Main App Component
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
            const response = await fetch('http://localhost:8000/search', {
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
            const response = await fetch(`http://localhost:8000/hotel/${hotelId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch hotel details');
            }
            const data = await response.json();
            // You can implement a modal or navigation to show detailed view
            console.log('Hotel details:', data);
        } catch (error) {
            console.error('Error fetching hotel details:', error);
        }
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-4xl font-bold text-center mb-8">Hotel Price Tracker</h1>
            
            <form onSubmit={handleSearch} className="max-w-lg mx-auto mb-8 space-y-4">
                <div>
                    <input
                        type="text"
                        name="location"
                        placeholder="Enter location"
                        value={searchParams.location}
                        onChange={handleInputChange}
                        className="w-full p-2 border rounded"
                        required
                    />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <input
                        type="date"
                        name="check_in"
                        value={searchParams.check_in}
                        onChange={handleInputChange}
                        className="p-2 border rounded"
                        required
                    />
                    <input
                        type="date"
                        name="check_out"
                        value={searchParams.check_out}
                        onChange={handleInputChange}
                        className="p-2 border rounded"
                        required
                    />
                </div>
                <div>
                    <input
                        type="number"
                        name="guests"
                        placeholder="Number of guests"
                        value={searchParams.guests}
                        onChange={handleInputChange}
                        className="w-full p-2 border rounded"
                        min="1"
                        required
                    />
                </div>
                <button
                    type="submit"
                    className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
                    disabled={loading}
                >
                    {loading ? 'Searching...' : 'Search Hotels'}
                </button>
            </form>

            {error && (
                <div className="text-red-500 text-center mb-4">
                    Error: {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
                {hotels.map(hotel => (
                    <HotelCard
                        key={hotel.hotel_id}
                        hotel={hotel}
                        onViewDetails={handleViewDetails}
                    />
                ))}
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));
