import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  TextField,
  Typography,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon,
  AttachMoney as MoneyIcon,
  Hotel as HotelIcon,
  Email as EmailIcon,
} from '@mui/icons-material';

function PriceAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`/api/alerts?email=${email}`);
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAlert = async (alertId) => {
    try {
      await fetch(`/api/alerts/${alertId}`, {
        method: 'DELETE',
      });
      setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
      // Show success notification
    } catch (error) {
      console.error('Error deleting alert:', error);
      // Show error notification
    }
  };

  const handleEmailSubmit = () => {
    setDialogOpen(false);
    setLoading(true);
    fetchAlerts();
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 3,
          }}
        >
          <Typography variant="h4">Price Alerts</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
          >
            View My Alerts
          </Button>
        </Box>

        {email ? (
          <Grid container spacing={3}>
            {alerts.map((alert) => (
              <Grid item xs={12} sm={6} md={4} key={alert.id}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                  }}
                >
                  <CardContent>
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        display: 'flex',
                        gap: 1,
                      }}
                    >
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteAlert(alert.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                    <Box sx={{ mb: 2 }}>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          mb: 1,
                        }}
                      >
                        <HotelIcon sx={{ mr: 1 }} color="action" />
                        <Typography variant="h6">{alert.hotel_name}</Typography>
                      </Box>
                      <Typography color="textSecondary">
                        {alert.hotel_location}
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        mb: 2,
                      }}
                    >
                      <MoneyIcon sx={{ mr: 1 }} color="action" />
                      <Typography variant="h5" color="primary">
                        Target: ${alert.target_price}
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      <EmailIcon sx={{ mr: 1 }} color="action" />
                      <Typography variant="body2" color="textSecondary">
                        {alert.email}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <Card sx={{ textAlign: 'center', py: 6 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                View Your Price Alerts
              </Typography>
              <Typography color="textSecondary" sx={{ mb: 3 }}>
                Enter your email to view and manage your price alerts
              </Typography>
              <Button
                variant="contained"
                startIcon={<EmailIcon />}
                onClick={() => setDialogOpen(true)}
              >
                Enter Email
              </Button>
            </CardContent>
          </Card>
        )}
      </Box>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>View Price Alerts</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            sx={{ mb: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleEmailSubmit}
            variant="contained"
            disabled={!email}
          >
            View Alerts
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default PriceAlerts;
