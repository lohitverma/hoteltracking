import React, { useState } from 'react';
import { Container, Grid, Paper, Typography, Box } from '@mui/material';
import SearchFilters from '../components/SearchFilters';
import HotelPriceTable from '../components/HotelPriceTable';
import RealTimePriceChart from '../components/RealTimePriceChart';
import HourlyPriceChart from '../components/HourlyPriceChart';

const Home = () => {
  const [searchParams, setSearchParams] = useState({
    location: '',
    checkIn: null,
    checkOut: null,
    priceRange: [0, 1000],
    hotelClass: [],
    amenities: []
  });

  const [selectedHotel, setSelectedHotel] = useState(null);

  const handleSearch = (params) => {
    setSearchParams(params);
    // TODO: Implement API call to fetch hotels
  };

  const handleHotelSelect = (hotel) => {
    setSelectedHotel(hotel);
    // TODO: Implement API call to fetch hotel details
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        {/* Search Filters */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <SearchFilters onSearch={handleSearch} />
          </Paper>
        </Grid>

        {/* Hotel Price Table */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Hotel Prices
            </Typography>
            <HotelPriceTable
              searchParams={searchParams}
              onHotelSelect={handleHotelSelect}
            />
          </Paper>
        </Grid>

        {/* Price Charts */}
        <Grid item xs={12} md={4}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Real-time Price Tracking
                </Typography>
                <RealTimePriceChart hotelId={selectedHotel?.id} />
              </Paper>
            </Grid>
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Price History
                </Typography>
                <HourlyPriceChart hotelId={selectedHotel?.id} />
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Home;
