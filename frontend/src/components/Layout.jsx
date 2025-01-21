import React from 'react';
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  Button,
  Container,
  useTheme,
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';

const Layout = ({ children }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, cursor: 'pointer' }}
            onClick={() => navigate('/page-city')}
          >
            Hotel Price Tracker
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              color="inherit"
              onClick={() => navigate('/page-city')}
              sx={{
                fontWeight: isActive('/page-city') ? 'bold' : 'normal',
                borderBottom: isActive('/page-city')
                  ? `2px solid ${theme.palette.common.white}`
                  : 'none',
              }}
            >
              Page City, AZ
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/search')}
              sx={{
                fontWeight: isActive('/search') ? 'bold' : 'normal',
                borderBottom: isActive('/search')
                  ? `2px solid ${theme.palette.common.white}`
                  : 'none',
              }}
            >
              Search Hotels
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Container
        component="main"
        maxWidth={false}
        sx={{
          flexGrow: 1,
          py: 3,
          px: { xs: 2, sm: 3 },
          bgcolor: 'background.default',
        }}
      >
        {children}
      </Container>

      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          backgroundColor: theme.palette.grey[100],
        }}
      >
        <Container maxWidth="sm">
          <Typography variant="body2" color="text.secondary" align="center">
            {new Date().getFullYear()} Hotel Price Tracker. All rights reserved.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;
