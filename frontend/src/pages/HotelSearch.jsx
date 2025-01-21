import React, { useState } from 'react';
import { Container, Grid, Paper, Typography, Box } from '@mui/material';
import SearchFilters from '../components/SearchFilters.jsx';
import HotelPriceTable from '../components/HotelPriceTable.jsx';

const HotelSearch = () => {
  const [searchParams, setSearchParams] = useState({
    location: '',
    checkIn: null,
    checkOut: null,
    priceRange: [0, 1000],
    hotelClass: [],
    amenities: []
  });

  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (params) => {
    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/hotels/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setSearchResults(data);
      setSearchParams(params);
    } catch (error) {
      console.error('Search error:', error);
      // You might want to show an error message to the user here
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        {/* Search Filters */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h5" gutterBottom>
              Search Hotels
            </Typography>
            <SearchFilters 
              onSearch={handleSearch} 
              initialValues={searchParams}
            />
          </Paper>
        </Grid>

        {/* Results */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h5" gutterBottom>
              Search Results
            </Typography>
            <HotelPriceTable 
              hotels={searchResults}
              loading={loading}
            />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default HotelSearch;
