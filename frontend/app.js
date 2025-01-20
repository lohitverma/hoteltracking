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

// AlertDialog Component
function AlertDialog({ hotel, onClose }) {
    const [formData, setFormData] = React.useState({
        price_threshold: hotel.price,
        email: '',
        phone: '',
        email_enabled: true,
        sms_enabled: false,
        push_enabled: true
    });
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/alerts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    hotel_id: hotel.id,
                    ...formData
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to create alert');
            }

            onClose();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
                <h2 className="text-xl font-bold mb-4">Set Price Alert</h2>
                <p className="mb-4">Get notified when {hotel.name} price drops below your target.</p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Price Threshold ($)
                        </label>
                        <input
                            type="number"
                            name="price_threshold"
                            value={formData.price_threshold}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Email
                        </label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Phone Number (optional)
                        </label>
                        <input
                            type="tel"
                            name="phone"
                            value={formData.phone}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        />
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center">
                            <input
                                type="checkbox"
                                name="email_enabled"
                                checked={formData.email_enabled}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <label className="ml-2 text-sm text-gray-700">
                                Email notifications
                            </label>
                        </div>

                        <div className="flex items-center">
                            <input
                                type="checkbox"
                                name="sms_enabled"
                                checked={formData.sms_enabled}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <label className="ml-2 text-sm text-gray-700">
                                SMS notifications
                            </label>
                        </div>

                        <div className="flex items-center">
                            <input
                                type="checkbox"
                                name="push_enabled"
                                checked={formData.push_enabled}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <label className="ml-2 text-sm text-gray-700">
                                Push notifications
                            </label>
                        </div>
                    </div>

                    {error && (
                        <div className="text-red-600 text-sm">
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end space-x-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
                        >
                            {loading ? 'Creating...' : 'Create Alert'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// HotelCard Component
function HotelCard({ hotel, onViewDetails }) {
    const [showPriceHistory, setShowPriceHistory] = React.useState(false);
    const [showAlertDialog, setShowAlertDialog] = React.useState(false);

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
                <button
                    className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                    onClick={() => setShowAlertDialog(true)}
                >
                    Set Alert
                </button>
            </div>
            {showPriceHistory && hotel.price_history && (
                <div className="mt-4">
                    <PriceChart priceHistory={hotel.price_history} />
                </div>
            )}
            {showAlertDialog && (
                <AlertDialog
                    hotel={hotel}
                    onClose={() => setShowAlertDialog(false)}
                />
            )}
        </div>
    );
}

// CitySelector Component
function CitySelector({ selectedCity, onCityChange }) {
    const [cities, setCities] = React.useState([]);
    const [searchTerm, setSearchTerm] = React.useState('');

    React.useEffect(() => {
        // Fetch cities from backend
        fetch('/api/cities')
            .then(res => res.json())
            .then(data => setCities(data))
            .catch(err => console.error('Error fetching cities:', err));
    }, []);

    return (
        <div className="relative w-full max-w-md">
            <input
                type="text"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Search for a city..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
            />
            <div className="absolute w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {cities
                    .filter(city => city.name.toLowerCase().includes(searchTerm.toLowerCase()))
                    .map(city => (
                        <div
                            key={city.id}
                            className="px-4 py-2 cursor-pointer hover:bg-gray-100"
                            onClick={() => onCityChange(city)}
                        >
                            {city.name}
                        </div>
                    ))
                }
            </div>
        </div>
    );
}

// ChatInterface Component
function ChatInterface({ selectedCity }) {
    const [messages, setMessages] = React.useState([]);
    const [inputMessage, setInputMessage] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const chatContainerRef = React.useRef(null);
    const [showChat, setShowChat] = React.useState(false);

    React.useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim()) return;

        const userMessage = inputMessage.trim();
        setInputMessage('');
        setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
        setLoading(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage,
                    city_id: selectedCity?.id
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();
            setMessages(prev => [...prev, { type: 'assistant', content: data.response }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                type: 'error',
                content: 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const toggleChat = () => {
        setShowChat(!showChat);
        if (!showChat && messages.length === 0) {
            // Add welcome message when opening chat for the first time
            setMessages([{
                type: 'assistant',
                content: 'Hello! I\'m your AI hotel assistant. I can help you find hotels, track prices, and provide recommendations. How can I assist you today?'
            }]);
        }
    };

    return (
        <>
            <button
                onClick={toggleChat}
                className="fixed bottom-4 right-4 bg-blue-600 text-white rounded-full p-4 shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
                <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                </svg>
            </button>

            {showChat && (
                <div className="fixed bottom-20 right-4 w-96 h-[600px] bg-white rounded-lg shadow-xl flex flex-col">
                    <div className="p-4 bg-blue-600 text-white rounded-t-lg flex justify-between items-center">
                        <h3 className="font-semibold">AI Hotel Assistant</h3>
                        <button
                            onClick={toggleChat}
                            className="text-white hover:text-gray-200 focus:outline-none"
                        >
                            <svg
                                className="w-5 h-5"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            </svg>
                        </button>
                    </div>

                    <div
                        ref={chatContainerRef}
                        className="flex-1 overflow-y-auto p-4 space-y-4"
                    >
                        {messages.map((message, index) => (
                            <div
                                key={index}
                                className={`flex ${
                                    message.type === 'user' ? 'justify-end' : 'justify-start'
                                }`}
                            >
                                <div
                                    className={`max-w-[80%] rounded-lg p-3 ${
                                        message.type === 'user'
                                            ? 'bg-blue-600 text-white'
                                            : message.type === 'error'
                                            ? 'bg-red-100 text-red-700'
                                            : 'bg-gray-100 text-gray-800'
                                    }`}
                                >
                                    {message.content}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex justify-start">
                                <div className="bg-gray-100 rounded-lg p-3 flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                            </div>
                        )}
                    </div>

                    <form onSubmit={handleSubmit} className="p-4 border-t">
                        <div className="flex space-x-2">
                            <input
                                type="text"
                                value={inputMessage}
                                onChange={(e) => setInputMessage(e.target.value)}
                                placeholder="Type your message..."
                                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <button
                                type="submit"
                                disabled={loading || !inputMessage.trim()}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                            >
                                Send
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </>
    );
}

// Main App Component
function App() {
    const [selectedCity, setSelectedCity] = React.useState(null);
    const [hotels, setHotels] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    React.useEffect(() => {
        // Get default city from user preferences or geolocation
        if (!selectedCity) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    try {
                        const response = await fetch(
                            `/api/cities/nearest?lat=${position.coords.latitude}&lon=${position.coords.longitude}`
                        );
                        const city = await response.json();
                        setSelectedCity(city);
                    } catch (err) {
                        console.error('Error getting default city:', err);
                        // Fallback to a default city
                        setSelectedCity({ id: 1, name: 'New York' });
                    }
                },
                (err) => {
                    console.error('Geolocation error:', err);
                    // Fallback to a default city
                    setSelectedCity({ id: 1, name: 'New York' });
                }
            );
        }
    }, []);

    React.useEffect(() => {
        if (selectedCity) {
            setLoading(true);
            fetch(`/api/hotels?city_id=${selectedCity.id}`)
                .then(res => res.json())
                .then(data => {
                    setHotels(data);
                    setLoading(false);
                })
                .catch(err => {
                    setError('Failed to fetch hotels. Please try again.');
                    setLoading(false);
                });
        }
    }, [selectedCity]);

    return (
        <div className="min-h-screen bg-gray-100">
            <nav className="bg-white shadow-lg">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex-shrink-0">
                            <h1 className="text-2xl font-bold text-gray-900">Hotel Tracker</h1>
                        </div>
                        <div className="ml-4 flex items-center md:ml-6">
                            <CitySelector
                                selectedCity={selectedCity}
                                onCityChange={setSelectedCity}
                            />
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                    </div>
                ) : error ? (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                        {error}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                        {hotels.map(hotel => (
                            <HotelCard
                                key={hotel.id}
                                hotel={hotel}
                                onViewDetails={() => {/* Handle view details */}}
                            />
                        ))}
                    </div>
                )}
            </main>
            <ChatInterface selectedCity={selectedCity} />
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));
