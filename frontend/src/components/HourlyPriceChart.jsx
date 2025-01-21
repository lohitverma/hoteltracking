import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  useTheme,
  Grid,
  Paper,
  IconButton,
  Tooltip,
  Fade,
  Chip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccessTime as TimeIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';

const HOURS = Array.from({ length: 14 }, (_, i) => i + 9); // 9 AM to 10 PM

function HourlyPriceChart({ city, hotels }) {
  const theme = useTheme();
  const [hourlyData, setHourlyData] = useState([]);
  const [selectedHour, setSelectedHour] = useState(null);
  const [hoveredHotel, setHoveredHotel] = useState(null);
  const currentHour = new Date().getHours();

  // Simulate real-time data updates
  useEffect(() => {
    const generateHourlyData = () => {
      const data = HOURS.map(hour => {
        const isCurrentHour = hour === currentHour;
        const hourData = {
          hour,
          timeLabel: `${hour % 12 || 12}${hour < 12 ? 'AM' : 'PM'}`,
          isCurrent: isCurrentHour,
        };

        hotels.forEach(hotel => {
          // Simulate price variations based on time of day
          const basePrice = hotel.price;
          const variation = isCurrentHour ? 0 : (Math.random() - 0.5) * 50;
          hourData[hotel.id] = Math.round(basePrice + variation);
        });

        return hourData;
      });
      setHourlyData(data);
    };

    generateHourlyData();
    const interval = setInterval(generateHourlyData, 300000); // Update every 5 minutes

    return () => clearInterval(interval);
  }, [hotels, currentHour]);

  const CustomBar = ({ x, y, width, height, fill, value, hotel }) => {
    const isHovered = hoveredHotel === hotel.id;
    
    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill={fill}
          opacity={isHovered ? 1 : 0.8}
          rx={4}
          ry={4}
          onMouseEnter={() => setHoveredHotel(hotel.id)}
          onMouseLeave={() => setHoveredHotel(null)}
        />
        <text
          x={x + width / 2}
          y={y - 4}
          textAnchor="middle"
          fill={theme.palette.text.primary}
          fontSize={12}
        >
          ${value}
        </text>
      </g>
    );
  };

  const TimeColumn = ({ hour, prices, isCurrentHour }) => {
    const maxPrice = Math.max(...Object.values(prices));
    const minPrice = Math.min(...Object.values(prices));
    const avgPrice = Math.round(
      Object.values(prices).reduce((a, b) => a + b, 0) / Object.values(prices).length
    );

    return (
      <Paper
        elevation={isCurrentHour ? 8 : 1}
        sx={{
          p: 2,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: isCurrentHour ? 'primary.light' : 'background.paper',
          color: isCurrentHour ? 'primary.contrastText' : 'text.primary',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: theme.shadows[8],
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <TimeIcon sx={{ mr: 1 }} />
          <Typography variant="h6">
            {hour % 12 || 12}{hour < 12 ? 'AM' : 'PM'}
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Chip
            label={`Max: $${maxPrice}`}
            color={isCurrentHour ? 'secondary' : 'default'}
            size="small"
          />
          <Chip
            label={`Avg: $${avgPrice}`}
            color={isCurrentHour ? 'secondary' : 'default'}
            variant="outlined"
            size="small"
          />
          <Chip
            label={`Min: $${minPrice}`}
            color={isCurrentHour ? 'secondary' : 'default'}
            variant="outlined"
            size="small"
          />
        </Box>
      </Paper>
    );
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Hourly Price Tracking - {city}
          </Typography>
          <Typography color="textSecondary">
            Showing prices from 9 AM to 10 PM
          </Typography>
        </Box>

        <Grid container spacing={2} sx={{ mb: 4 }}>
          {HOURS.map(hour => {
            const hourData = hourlyData.find(d => d.hour === hour) || {};
            const prices = Object.fromEntries(
              Object.entries(hourData).filter(([key]) => 
                hotels.some(h => h.id.toString() === key)
              )
            );
            
            return (
              <Grid item xs={12} sm={6} md={4} lg={2} key={hour}>
                <TimeColumn
                  hour={hour}
                  prices={prices}
                  isCurrentHour={hour === currentHour}
                />
              </Grid>
            );
          })}
        </Grid>

        <Box sx={{ height: 400, width: '100%', mt: 4 }}>
          <ResponsiveContainer>
            <BarChart
              data={hourlyData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timeLabel"
                tick={{ fill: theme.palette.text.primary }}
              />
              <YAxis
                tick={{ fill: theme.palette.text.primary }}
                label={{
                  value: 'Price ($)',
                  angle: -90,
                  position: 'insideLeft',
                  fill: theme.palette.text.primary,
                }}
              />
              {hotels.map((hotel, index) => (
                <Bar
                  key={hotel.id}
                  dataKey={hotel.id}
                  fill={theme.palette.primary.main}
                  shape={<CustomBar hotel={hotel} />}
                  stackId="stack"
                >
                  {hourlyData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.isCurrent
                          ? theme.palette.secondary.main
                          : theme.palette.primary.main
                      }
                    />
                  ))}
                </Bar>
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Box>

        <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {hotels.map((hotel) => (
            <Chip
              key={hotel.id}
              label={hotel.name}
              onDelete={() => {}}
              onClick={() => {}}
              sx={{
                bgcolor: hoveredHotel === hotel.id ? 'primary.main' : 'transparent',
                color: hoveredHotel === hotel.id ? 'primary.contrastText' : 'text.primary',
                '&:hover': {
                  bgcolor: 'primary.light',
                  color: 'primary.contrastText',
                },
              }}
            />
          ))}
        </Box>
      </CardContent>
    </Card>
  );
}

export default HourlyPriceChart;
