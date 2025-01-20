import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  useTheme,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Chip,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

const COLORS = [
  '#2196f3',
  '#f50057',
  '#00bcd4',
  '#4caf50',
  '#ff9800',
  '#9c27b0',
  '#795548',
  '#607d8b',
];

function RealTimePriceChart({ city }) {
  const theme = useTheme();
  const [ws, setWs] = useState(null);
  const [priceData, setPriceData] = useState(null);
  const [selectedHotels, setSelectedHotels] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [viewMode, setViewMode] = useState('realtime'); // realtime or historical

  useEffect(() => {
    if (!city) return;

    // Connect to WebSocket
    const websocket = new WebSocket(`ws://localhost:8000/api/ws/prices/${city}`);

    websocket.onopen = () => {
      console.log('Connected to price tracking websocket');
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPriceData(data);
      
      // Update chart data
      if (data.current_prices) {
        const timestamp = new Date(data.timestamp);
        
        setChartData(prevData => {
          const newPoint = {
            timestamp,
            ...Object.keys(data.current_prices).reduce((acc, hotelId) => {
              acc[hotelId] = data.current_prices[hotelId].current_price;
              return acc;
            }, {})
          };

          // Keep last 50 points for real-time view
          const updatedData = [...(prevData || []), newPoint];
          return updatedData.slice(-50);
        });
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('Disconnected from price tracking websocket');
    };

    setWs(websocket);

    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [city]);

  const handleHotelToggle = (hotelId) => {
    setSelectedHotels(prev => {
      if (prev.includes(hotelId)) {
        return prev.filter(id => id !== hotelId);
      }
      return [...prev, hotelId];
    });
  };

  const getHotelColor = useCallback((index) => {
    return COLORS[index % COLORS.length];
  }, []);

  const renderPriceStatistics = () => {
    if (!priceData?.current_prices) return null;

    return (
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(priceData.current_prices).map(([hotelId, data], index) => (
          <Grid item xs={12} sm={6} md={4} key={hotelId}>
            <Card
              sx={{
                cursor: 'pointer',
                bgcolor: selectedHotels.includes(hotelId) 
                  ? `${getHotelColor(index)}15`
                  : 'background.paper',
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: theme.shadows[4],
                },
              }}
              onClick={() => handleHotelToggle(hotelId)}
            >
              <CardContent>
                <Typography variant="h6" gutterBottom noWrap>
                  {data.hotel_name}
                </Typography>
                <Typography variant="h5" color="primary" gutterBottom>
                  ${data.current_price}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip
                    size="small"
                    icon={data.current_price > data.avg_price ? <TrendingUp /> : <TrendingDown />}
                    label={`Avg: $${Math.round(data.avg_price)}`}
                    color={data.current_price > data.avg_price ? 'error' : 'success'}
                  />
                  <Chip
                    size="small"
                    label={`Min: $${data.min_price}`}
                    variant="outlined"
                  />
                  <Chip
                    size="small"
                    label={`Max: $${data.max_price}`}
                    variant="outlined"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  const renderChart = () => {
    if (!chartData?.length || !priceData?.current_prices) return null;

    const selectedData = viewMode === 'realtime' 
      ? chartData 
      : Object.values(priceData.historical_trends)[0]?.dates.map((date, index) => ({
          timestamp: new Date(date),
          ...Object.keys(priceData.historical_trends).reduce((acc, hotelId) => {
            acc[hotelId] = priceData.historical_trends[hotelId].prices[index];
            return acc;
          }, {})
        }));

    return (
      <Box sx={{ height: 400, width: '100%' }}>
        <ResponsiveContainer>
          <LineChart data={selectedData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(timestamp) => {
                const date = new Date(timestamp);
                return viewMode === 'realtime'
                  ? format(date, 'HH:mm:ss')
                  : format(date, 'MMM d');
              }}
            />
            <YAxis />
            <Tooltip
              labelFormatter={(timestamp) => {
                const date = new Date(timestamp);
                return viewMode === 'realtime'
                  ? format(date, 'HH:mm:ss')
                  : format(date, 'MMM d, yyyy');
              }}
              formatter={(value, name) => [
                `$${value}`,
                priceData.current_prices[name]?.hotel_name
              ]}
            />
            <Legend />
            {selectedHotels.map((hotelId, index) => (
              <Line
                key={hotelId}
                type="monotone"
                dataKey={hotelId}
                name={priceData.current_prices[hotelId]?.hotel_name}
                stroke={getHotelColor(index)}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </Box>
    );
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Real-Time Price Tracking - {city}
          </Typography>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>View Mode</InputLabel>
            <Select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              label="View Mode"
            >
              <MenuItem value="realtime">Real-Time (Last Hour)</MenuItem>
              <MenuItem value="historical">Historical (30 Days)</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {renderPriceStatistics()}
        {renderChart()}
      </CardContent>
    </Card>
  );
}

export default RealTimePriceChart;
