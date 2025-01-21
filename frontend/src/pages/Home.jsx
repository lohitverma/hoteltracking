import React from 'react';
import { Container, Typography, Box, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Welcome to Hotel Price Tracker
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph>
          Track hotel prices, set alerts, and find the best deals for your next stay.
        </Typography>
        <Box sx={{ mt: 4 }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={() => navigate('/search')}
            sx={{ mr: 2 }}
          >
            Search Hotels
          </Button>
          <Button
            variant="outlined"
            color="primary"
            size="large"
            onClick={() => navigate('/alerts')}
          >
            View Price Alerts
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default Home;
