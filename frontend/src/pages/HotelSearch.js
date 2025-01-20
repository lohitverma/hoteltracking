import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Rating,
  Button,
  Chip,
  useTheme,
  Fade,
  Divider,
  Stack,
} from '@mui/material';
import {
  LocationOn as LocationIcon,
  AttachMoney as PriceIcon,
  Bed as BedIcon,
  Person as PersonIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import HotelPriceTable from '../components/HotelPriceTable';
import SearchFilters from '../components/SearchFilters';

function HotelSearch() {
  const theme = useTheme();
  const [searchParams, setSearchParams] = useState({
    city: '',
    checkIn: null,
    checkOut: null,
    guests: 2,
    rooms: 1,
    priceRange: [0, 1000],
    selectedAmenities: [],
    minRating: 0,
  });

  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showPriceChart, setShowPriceChart] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      // Simulated API call
      const response = await new Promise((resolve) => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              name: 'Luxury Resort & Spa',
              rating: 4.5,
              price: 299,
              image: 'https://source.unsplash.com/800x600/?hotel,luxury',
              location: 'Downtown',
              amenities: ['Pool', 'Spa', 'Restaurant'],
            },
            {
              id: 2,
              name: 'Business Hotel Elite',
              rating: 4.0,
              price: 199,
              image: 'https://source.unsplash.com/800x600/?hotel,business',
              location: 'Financial District',
              amenities: ['WiFi', 'Gym', 'Restaurant'],
            },
            {
              id: 3,
              name: 'Seaside Resort',
              rating: 4.8,
              price: 399,
              image: 'https://source.unsplash.com/800x600/?hotel,beach',
              location: 'Beachfront',
              amenities: ['Pool', 'Spa', 'Beach Access'],
            },
          ]);
        }, 1500);
      });

      setHotels(response);
      setShowPriceChart(true);
    } catch (error) {
      console.error('Error fetching hotels:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography
          variant="h3"
          component="h1"
          gutterBottom
          sx={{
            fontWeight: 700,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            textFillColor: 'transparent',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Find Your Perfect Stay
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
          Compare prices, track changes, and book with confidence
        </Typography>
      </Box>

      <SearchFilters
        searchParams={searchParams}
        setSearchParams={setSearchParams}
        onSearch={handleSearch}
        loading={loading}
      />

      {showPriceChart && searchParams.city && hotels.length > 0 && (
        <Fade in timeout={1000}>
          <Box sx={{ mb: 4 }}>
            <HotelPriceTable city={searchParams.city} hotels={hotels} />
          </Box>
        </Fade>
      )}

      <Grid container spacing={3}>
        {hotels.map((hotel) => (
          <Grid item xs={12} md={6} lg={4} key={hotel.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                },
              }}
            >
              <CardMedia
                component="img"
                height="240"
                image={hotel.image}
                alt={hotel.name}
                sx={{ objectFit: 'cover' }}
              />
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h5" component="h2" gutterBottom>
                  {hotel.name}
                </Typography>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Rating value={hotel.rating} precision={0.5} readOnly />
                    <Typography variant="body2" color="text.secondary">
                      ({hotel.rating})
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocationIcon color="primary" />
                    <Typography variant="body2">{hotel.location}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PriceIcon color="primary" />
                    <Typography variant="h6">${hotel.price}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      per night
                    </Typography>
                  </Box>
                  <Divider />
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {hotel.amenities.map((amenity) => (
                      <Chip
                        key={amenity}
                        label={amenity}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Stack>
              </CardContent>
              <Box sx={{ p: 2 }}>
                <Button
                  fullWidth
                  variant="contained"
                  endIcon={<ArrowForwardIcon />}
                  sx={{
                    borderRadius: '8px',
                    textTransform: 'none',
                  }}
                >
                  View Details
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}

export default HotelSearch;
