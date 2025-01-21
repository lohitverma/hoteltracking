import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import RealTimeHotelChart from '../components/RealTimeHotelChart';

const PageCity = () => {
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Page City, Arizona
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time hotel price tracking for 2-star hotels. Prices are updated every minute.
        </Typography>
      </Box>
      <RealTimeHotelChart />
    </Container>
  );
};

export default PageCity;
