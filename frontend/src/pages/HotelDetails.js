import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Rating,
  TextField,
  Typography,
  useTheme,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  AttachMoney as MoneyIcon,
  LocationOn as LocationIcon,
  Pool as PoolIcon,
  Wifi as WifiIcon,
  Restaurant as RestaurantIcon,
  LocalParking as ParkingIcon,
  Spa as SpaIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';

const amenityIcons = {
  Pool: <PoolIcon />,
  WiFi: <WifiIcon />,
  Restaurant: <RestaurantIcon />,
  Parking: <ParkingIcon />,
  Spa: <SpaIcon />,
};

function HotelDetails() {
  const { id } = useParams();
  const theme = useTheme();
  const [hotel, setHotel] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [priceTrends, setPriceTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [alertDialogOpen, setAlertDialogOpen] = useState(false);
  const [alertEmail, setAlertEmail] = useState('');
  const [alertPrice, setAlertPrice] = useState('');

  useEffect(() => {
    const fetchHotelData = async () => {
      try {
        const [hotelResponse, historyResponse, trendsResponse] = await Promise.all([
          fetch(`/api/hotels/${id}`),
          fetch(`/api/hotels/${id}/price-history`),
          fetch(`/api/hotels/${id}/price-trends`),
        ]);

        const [hotelData, historyData, trendsData] = await Promise.all([
          hotelResponse.json(),
          historyResponse.json(),
          trendsResponse.json(),
        ]);

        setHotel(hotelData);
        setPriceHistory(historyData);
        setPriceTrends(trendsData);
      } catch (error) {
        console.error('Error fetching hotel data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHotelData();
  }, [id]);

  const handleCreateAlert = async () => {
    try {
      await fetch('/api/alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          hotel_id: id,
          email: alertEmail,
          target_price: parseFloat(alertPrice),
        }),
      });
      setAlertDialogOpen(false);
      // Show success notification
    } catch (error) {
      console.error('Error creating alert:', error);
      // Show error notification
    }
  };

  if (loading || !hotel) {
    return (
      <Container>
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Grid container spacing={4}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardMedia
              component="img"
              height="400"
              image={hotel.image_url}
              alt={hotel.name}
            />
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h4" component="h1">
                  {hotel.name}
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<NotificationsIcon />}
                  onClick={() => setAlertDialogOpen(true)}
                >
                  Set Price Alert
                </Button>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <LocationIcon sx={{ mr: 1 }} color="action" />
                <Typography color="textSecondary">{hotel.location}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Rating value={hotel.rating} precision={0.5} readOnly />
                <Typography variant="body2" sx={{ ml: 1 }} color="textSecondary">
                  ({hotel.review_count} reviews)
                </Typography>
              </Box>
              <Typography variant="h5" color="primary" sx={{ mb: 3 }}>
                <MoneyIcon sx={{ mr: 1, verticalAlign: 'bottom' }} />
                ${hotel.price}/night
              </Typography>
              <Typography variant="h6" gutterBottom>
                Amenities
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                {hotel.amenities.map((amenity) => (
                  <Chip
                    key={amenity}
                    label={amenity}
                    icon={amenityIcons[amenity]}
                    variant="outlined"
                  />
                ))}
              </Box>
              <Typography variant="h6" gutterBottom>
                Price History
              </Typography>
              <Box sx={{ height: 300, mb: 3 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={priceHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(date) => format(new Date(date), 'MMM d')}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(date) =>
                        format(new Date(date), 'MMM d, yyyy')
                      }
                      formatter={(value) => [`$${value}`, 'Price']}
                    />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke={theme.palette.primary.main}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Price Trends
              </Typography>
              {priceTrends && (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Average Price
                    </Typography>
                    <Typography variant="h5" color="primary">
                      ${priceTrends.average_price}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Lowest Price (30 days)
                    </Typography>
                    <Typography variant="h5" color="success.main">
                      ${priceTrends.lowest_price}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">
                      Price Trend
                    </Typography>
                    <Typography
                      variant="h5"
                      color={
                        priceTrends.trend === 'increasing'
                          ? 'error.main'
                          : 'success.main'
                      }
                    >
                      {priceTrends.trend.charAt(0).toUpperCase() +
                        priceTrends.trend.slice(1)}
                    </Typography>
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Hotel Description
              </Typography>
              <Typography color="textSecondary">
                {hotel.description}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog
        open={alertDialogOpen}
        onClose={() => setAlertDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Set Price Alert</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            value={alertEmail}
            onChange={(e) => setAlertEmail(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Target Price"
            type="number"
            fullWidth
            value={alertPrice}
            onChange={(e) => setAlertPrice(e.target.value)}
            InputProps={{
              startAdornment: <MoneyIcon sx={{ mr: 1 }} color="action" />,
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAlertDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateAlert}
            variant="contained"
            disabled={!alertEmail || !alertPrice}
          >
            Create Alert
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default HotelDetails;
