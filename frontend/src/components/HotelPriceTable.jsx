import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  useTheme,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Rating,
  IconButton,
  Tooltip,
  Collapse,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Timeline as TimelineIcon,
  Star as StarIcon,
  Info as InfoIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

const HOURS = Array.from({ length: 14 }, (_, i) => i + 9); // 9 AM to 10 PM

function HotelRow({ hotel, hourlyPrices, currentHour }) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  const basePrice = hotel.price;

  const getPriceColor = (price) => {
    if (price > basePrice) return theme.palette.error.main;
    if (price < basePrice) return theme.palette.success.main;
    return theme.palette.text.primary;
  };

  const getPriceTrend = (price) => {
    if (price > basePrice) return <TrendingUpIcon color="error" />;
    if (price < basePrice) return <TrendingDownIcon color="success" />;
    return null;
  };

  const getMinMaxAvg = () => {
    const prices = Object.values(hourlyPrices);
    return {
      min: Math.min(...prices),
      max: Math.max(...prices),
      avg: Math.round(prices.reduce((a, b) => a + b, 0) / prices.length),
    };
  };

  const { min, max, avg } = getMinMaxAvg();

  return (
    <>
      <TableRow
        sx={{
          '&:hover': {
            bgcolor: 'action.hover',
          },
          cursor: 'pointer',
        }}
        onClick={() => setOpen(!open)}
      >
        <TableCell component="th" scope="row" sx={{ width: '300px' }}>
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
              {hotel.name}
            </Typography>
            <Rating value={hotel.rating} precision={0.5} size="small" readOnly />
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip
                size="small"
                label={`Base: $${basePrice}`}
                color="primary"
                variant="outlined"
              />
              <Tooltip title="Average price across all hours">
                <Chip
                  size="small"
                  label={`Avg: $${avg}`}
                  color={avg > basePrice ? 'error' : 'success'}
                  variant="outlined"
                />
              </Tooltip>
            </Box>
          </Box>
        </TableCell>
        {HOURS.map(hour => {
          const price = hourlyPrices[hour];
          const isCurrent = hour === currentHour;
          
          return (
            <TableCell
              key={hour}
              align="center"
              sx={{
                bgcolor: isCurrent ? 'primary.light' : 'inherit',
                color: isCurrent ? 'primary.contrastText' : 'inherit',
                fontWeight: isCurrent ? 'bold' : 'normal',
                position: 'relative',
                minWidth: '100px',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                <Typography
                  sx={{
                    color: isCurrent ? 'inherit' : getPriceColor(price),
                    fontWeight: 'bold',
                  }}
                >
                  ${price}
                </Typography>
                {getPriceTrend(price)}
              </Box>
              {isCurrent && (
                <LinearProgress
                  sx={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                  }}
                />
              )}
            </TableCell>
          );
        })}
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={15}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 2 }}>
              <Typography variant="h6" gutterBottom>
                Price Analysis
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Paper sx={{ p: 2, flex: 1 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Lowest Price
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    ${min}
                  </Typography>
                  <Typography variant="caption" display="block">
                    {((basePrice - min) / basePrice * 100).toFixed(1)}% below base price
                  </Typography>
                </Paper>
                <Paper sx={{ p: 2, flex: 1 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Average Price
                  </Typography>
                  <Typography variant="h6">
                    ${avg}
                  </Typography>
                  <Typography variant="caption" display="block">
                    {((avg - basePrice) / basePrice * 100).toFixed(1)}% difference from base
                  </Typography>
                </Paper>
                <Paper sx={{ p: 2, flex: 1 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Highest Price
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    ${max}
                  </Typography>
                  <Typography variant="caption" display="block">
                    {((max - basePrice) / basePrice * 100).toFixed(1)}% above base price
                  </Typography>
                </Paper>
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

function HotelPriceTable({ city, hotels }) {
  const theme = useTheme();
  const [hourlyPrices, setHourlyPrices] = useState({});
  const currentHour = new Date().getHours();

  useEffect(() => {
    const generateHourlyPrices = () => {
      const prices = {};
      hotels.forEach(hotel => {
        prices[hotel.id] = {};
        HOURS.forEach(hour => {
          const isCurrentHour = hour === currentHour;
          const basePrice = hotel.price;
          const variation = isCurrentHour ? 0 : (Math.random() - 0.5) * 50;
          prices[hotel.id][hour] = Math.round(basePrice + variation);
        });
      });
      setHourlyPrices(prices);
    };

    generateHourlyPrices();
    const interval = setInterval(generateHourlyPrices, 300000); // Update every 5 minutes

    return () => clearInterval(interval);
  }, [hotels, currentHour]);

  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Typography variant="h5" gutterBottom>
              Hotel Price Comparison - {city}
            </Typography>
            <Typography color="textSecondary">
              Showing hourly prices from 9 AM to 10 PM
            </Typography>
          </div>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Current hour prices are highlighted">
              <Chip
                icon={<TimelineIcon />}
                label="Real-time Updates"
                color="primary"
              />
            </Tooltip>
            <Tooltip title="Click on a hotel row to see detailed price analysis">
              <Chip
                icon={<InfoIcon />}
                label="Show Details"
                variant="outlined"
              />
            </Tooltip>
          </Box>
        </Box>

        <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Hotel</TableCell>
                {HOURS.map(hour => (
                  <TableCell
                    key={hour}
                    align="center"
                    sx={{
                      bgcolor: hour === currentHour ? 'primary.main' : 'inherit',
                      color: hour === currentHour ? 'primary.contrastText' : 'inherit',
                    }}
                  >
                    <Typography variant="subtitle2">
                      {hour % 12 || 12}
                      {hour < 12 ? 'AM' : 'PM'}
                    </Typography>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {hotels.map(hotel => (
                <HotelRow
                  key={hotel.id}
                  hotel={hotel}
                  hourlyPrices={hourlyPrices[hotel.id] || {}}
                  currentHour={currentHour}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="textSecondary">
            * Prices are updated every 5 minutes. Click on a hotel row to view detailed price analysis.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

export default HotelPriceTable;
