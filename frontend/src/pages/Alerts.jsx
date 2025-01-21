import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem
} from '@mui/material';
import { Delete as DeleteIcon, Edit as EditIcon } from '@mui/icons-material';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [formData, setFormData] = useState({
    hotelId: '',
    targetPrice: '',
    condition: 'below', // 'below' or 'above'
    email: ''
  });

  useEffect(() => {
    // TODO: Fetch alerts from API
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      // TODO: Implement API call
      const response = await fetch('/api/alerts');
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const handleOpenDialog = (alert = null) => {
    if (alert) {
      setFormData({
        hotelId: alert.hotelId,
        targetPrice: alert.targetPrice,
        condition: alert.condition,
        email: alert.email
      });
      setSelectedAlert(alert);
    } else {
      setFormData({
        hotelId: '',
        targetPrice: '',
        condition: 'below',
        email: ''
      });
      setSelectedAlert(null);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedAlert(null);
  };

  const handleSubmit = async () => {
    try {
      if (selectedAlert) {
        // Update existing alert
        await fetch(`/api/alerts/${selectedAlert.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
      } else {
        // Create new alert
        await fetch('/api/alerts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
      }
      fetchAlerts();
      handleCloseDialog();
    } catch (error) {
      console.error('Error saving alert:', error);
    }
  };

  const handleDelete = async (alertId) => {
    try {
      await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' });
      fetchAlerts();
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Price Alerts
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={() => handleOpenDialog()}
              sx={{ mb: 2 }}
            >
              Create New Alert
            </Button>
            <List>
              {alerts.map((alert) => (
                <ListItem key={alert.id}>
                  <ListItemText
                    primary={`${alert.hotelName} - ${alert.condition} ${alert.targetPrice}`}
                    secondary={alert.email}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      aria-label="edit"
                      onClick={() => handleOpenDialog(alert)}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      edge="end"
                      aria-label="delete"
                      onClick={() => handleDelete(alert.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>

      {/* Alert Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>
          {selectedAlert ? 'Edit Alert' : 'Create New Alert'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Hotel ID"
            value={formData.hotelId}
            onChange={(e) =>
              setFormData({ ...formData, hotelId: e.target.value })
            }
            margin="normal"
          />
          <TextField
            fullWidth
            label="Target Price"
            type="number"
            value={formData.targetPrice}
            onChange={(e) =>
              setFormData({ ...formData, targetPrice: e.target.value })
            }
            margin="normal"
          />
          <TextField
            fullWidth
            select
            label="Condition"
            value={formData.condition}
            onChange={(e) =>
              setFormData({ ...formData, condition: e.target.value })
            }
            margin="normal"
          >
            <MenuItem value="below">Below</MenuItem>
            <MenuItem value="above">Above</MenuItem>
          </TextField>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} color="primary">
            {selectedAlert ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Alerts;
