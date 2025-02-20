import React, { useState, useEffect } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  Tooltip,
  Fade,
  CircularProgress,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

// Mock data for development
const mockHotelData = [
  {
    id: 1,
    name: "Budget Inn",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (120 - 80) + 80),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 2,
    name: "Travelers Lodge",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (130 - 90) + 90),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 3,
    name: "Lake Powell Inn",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (140 - 95) + 95),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 4,
    name: "Desert View Motel",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (110 - 75) + 75),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 5,
    name: "Canyon Lodge",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (125 - 85) + 85),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 6,
    name: "Arizona Motor Inn",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (115 - 80) + 80),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 7,
    name: "Page View Hotel",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (135 - 95) + 95),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 8,
    name: "Antelope Inn",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (120 - 85) + 85),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 9,
    name: "Glen Canyon Motel",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (125 - 90) + 90),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  },
  {
    id: 10,
    name: "Powell Place Inn",
    rating: 2,
    priceHistory: Array(10).fill(null).map((_, i) => ({
      amount: Math.floor(Math.random() * (130 - 85) + 85),
      available: Math.random() > 0.2,
      changed: Math.random() > 0.7
    }))
  }
];

const HOURS_TO_SHOW = 10;
const UPDATE_INTERVAL = 60000; // 1 minute

const RealTimeHotelChart = () => {
  const [hotelData, setHotelData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Generate column headers (last 10 hours)
  const getTimeColumns = () => {
    const columns = [];
    const now = new Date();
    for (let i = HOURS_TO_SHOW - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setHours(now.getHours() - i);
      columns.push(date);
    }
    return columns;
  };

  const fetchHotelData = async () => {
    try {
      // For development, use mock data
      setHotelData(mockHotelData);
      setLastUpdate(new Date());
      setLoading(false);
      
      // TODO: Replace with actual API call when backend is ready
      /*
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/hotels/page-city`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch hotel data');
      }

      const data = await response.json();
      setHotelData(data);
      setLastUpdate(new Date());
      */
    } catch (error) {
      console.error('Error fetching hotel data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHotelData();
    const interval = setInterval(fetchHotelData, UPDATE_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  const getPriceChangeIndicator = (current, previous) => {
    if (!previous) return null;
    if (current > previous) {
      return (
        <Tooltip title={`Increased from $${previous}`}>
          <TrendingUpIcon color="error" fontSize="small" />
        </Tooltip>
      );
    }
    if (current < previous) {
      return (
        <Tooltip title={`Decreased from $${previous}`}>
          <TrendingDownIcon color="success" fontSize="small" />
        </Tooltip>
      );
    }
    return null;
  };

  const getAvailabilityIndicator = (available) => {
    return available ? (
      <Tooltip title="Available">
        <CheckCircleIcon color="success" fontSize="small" />
      </Tooltip>
    ) : (
      <Tooltip title="Not Available">
        <CancelIcon color="error" fontSize="small" />
      </Tooltip>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6">
          Page City, Arizona - 2-Star Hotels Real-Time Prices
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Last updated: {format(lastUpdate, 'HH:mm:ss')}
        </Typography>
      </Box>

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Hotel Name</TableCell>
              {getTimeColumns().map((date) => (
                <TableCell key={date.getTime()} align="center">
                  {format(date, 'HH:mm')}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {hotelData.map((hotel) => (
              <TableRow
                key={hotel.id}
                sx={{
                  '&:last-child td, &:last-child th': { border: 0 },
                  '&:hover': { backgroundColor: 'action.hover' },
                }}
              >
                <TableCell component="th" scope="row">
                  <Tooltip
                    title={
                      <Box>
                        <Typography variant="body2">{hotel.name}</Typography>
                        <Typography variant="caption">
                          Rating: {hotel.rating} 
                        </Typography>
                      </Box>
                    }
                  >
                    <Box>{hotel.name}</Box>
                  </Tooltip>
                </TableCell>
                {hotel.priceHistory.map((price, index) => (
                  <TableCell
                    key={index}
                    align="center"
                    sx={{
                      position: 'relative',
                      transition: 'background-color 0.3s',
                    }}
                  >
                    <Fade in timeout={500}>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 0.5,
                        }}
                      >
                        <Typography
                          sx={{
                            color: price.changed ? 'warning.main' : 'inherit',
                            fontWeight: price.changed ? 'bold' : 'normal',
                          }}
                        >
                          ${price.amount}
                        </Typography>
                        {getPriceChangeIndicator(
                          price.amount,
                          index > 0 ? hotel.priceHistory[index - 1].amount : null
                        )}
                        {getAvailabilityIndicator(price.available)}
                      </Box>
                    </Fade>
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default RealTimeHotelChart;
