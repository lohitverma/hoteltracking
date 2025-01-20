import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
  useTheme,
} from '@mui/material';
import {
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  Chat as ChatIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

const features = [
  {
    title: 'Search Hotels',
    description: 'Find the perfect hotel with our powerful search engine.',
    icon: <SearchIcon sx={{ fontSize: 40 }} />,
    path: '/search',
    color: '#2196f3',
  },
  {
    title: 'Price Alerts',
    description: 'Get notified when hotel prices drop to your target price.',
    icon: <NotificationsIcon sx={{ fontSize: 40 }} />,
    path: '/alerts',
    color: '#f50057',
  },
  {
    title: 'Chat Assistant',
    description: 'Get personalized hotel recommendations from our AI assistant.',
    icon: <ChatIcon sx={{ fontSize: 40 }} />,
    path: '/chat',
    color: '#00bcd4',
  },
  {
    title: 'Price Trends',
    description: 'Analyze historical price trends to find the best time to book.',
    icon: <TrendingUpIcon sx={{ fontSize: 40 }} />,
    path: '/search',
    color: '#4caf50',
  },
];

function Home() {
  const theme = useTheme();
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 8 }}>
        <Typography
          variant="h1"
          align="center"
          sx={{
            mb: 2,
            fontSize: { xs: '2.5rem', md: '3.5rem' },
            fontWeight: 700,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Track Hotel Prices
        </Typography>
        <Typography
          variant="h5"
          align="center"
          color="textSecondary"
          sx={{ mb: 4 }}
        >
          Find the best hotel deals and never overpay again
        </Typography>
        <Box
          display="flex"
          justifyContent="center"
          gap={2}
          sx={{ mb: 6 }}
        >
          <Button
            variant="contained"
            size="large"
            startIcon={<SearchIcon />}
            onClick={() => navigate('/search')}
          >
            Search Hotels
          </Button>
          <Button
            variant="outlined"
            size="large"
            startIcon={<NotificationsIcon />}
            onClick={() => navigate('/alerts')}
          >
            Set Price Alert
          </Button>
        </Box>
      </Box>

      <Grid container spacing={4}>
        {features.map((feature) => (
          <Grid item xs={12} sm={6} md={3} key={feature.title}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: theme.shadows[8],
                },
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    mb: 2,
                  }}
                >
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: '50%',
                      backgroundColor: `${feature.color}20`,
                      color: feature.color,
                    }}
                  >
                    {feature.icon}
                  </Box>
                </Box>
                <Typography
                  gutterBottom
                  variant="h6"
                  component="h2"
                  align="center"
                >
                  {feature.title}
                </Typography>
                <Typography
                  variant="body2"
                  color="textSecondary"
                  align="center"
                >
                  {feature.description}
                </Typography>
              </CardContent>
              <Box sx={{ flexGrow: 1 }} />
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Button
                  variant="text"
                  color="primary"
                  onClick={() => navigate(feature.path)}
                >
                  Learn More
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 8, mb: 4 }}>
        <Typography variant="h4" align="center" gutterBottom>
          Why Choose Us?
        </Typography>
        <Grid container spacing={4} sx={{ mt: 2 }}>
          <Grid item xs={12} md={4}>
            <Box textAlign="center">
              <Typography variant="h6" gutterBottom>
                Real-time Price Tracking
              </Typography>
              <Typography color="textSecondary">
                Monitor hotel prices 24/7 and get instant notifications when prices drop.
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box textAlign="center">
              <Typography variant="h6" gutterBottom>
                Smart Recommendations
              </Typography>
              <Typography color="textSecondary">
                Get personalized hotel suggestions based on your preferences and budget.
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box textAlign="center">
              <Typography variant="h6" gutterBottom>
                Price History Analysis
              </Typography>
              <Typography color="textSecondary">
                Make informed decisions with historical price data and trends.
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}

export default Home;
