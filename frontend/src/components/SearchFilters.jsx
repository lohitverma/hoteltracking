import React, { useState } from 'react';
import {
  Grid,
  TextField,
  Button,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  Typography,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';

const SearchFilters = ({ onSearch, initialValues }) => {
  const [filters, setFilters] = useState(initialValues || {
    location: '',
    checkIn: null,
    checkOut: null,
    priceRange: [0, 1000],
    hotelClass: [],
    amenities: []
  });

  const amenitiesList = [
    'WiFi',
    'Pool',
    'Spa',
    'Gym',
    'Restaurant',
    'Room Service',
    'Parking',
    'Beach Access'
  ];

  const handleChange = (field) => (event) => {
    setFilters({
      ...filters,
      [field]: event.target.value
    });
  };

  const handleDateChange = (field) => (date) => {
    setFilters({
      ...filters,
      [field]: date
    });
  };

  const handlePriceChange = (event, newValue) => {
    setFilters({
      ...filters,
      priceRange: newValue
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSearch(filters);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Location"
            value={filters.location}
            onChange={handleChange('location')}
            placeholder="Enter city or hotel name"
          />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <DatePicker
            label="Check-in Date"
            value={filters.checkIn}
            onChange={handleDateChange('checkIn')}
            renderInput={(params) => <TextField {...params} fullWidth />}
            minDate={new Date()}
          />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <DatePicker
            label="Check-out Date"
            value={filters.checkOut}
            onChange={handleDateChange('checkOut')}
            renderInput={(params) => <TextField {...params} fullWidth />}
            minDate={filters.checkIn || new Date()}
          />
        </Grid>

        <Grid item xs={12}>
          <Typography gutterBottom>Price Range: ${filters.priceRange[0]} - ${filters.priceRange[1]}</Typography>
          <Slider
            value={filters.priceRange}
            onChange={handlePriceChange}
            valueLabelDisplay="auto"
            min={0}
            max={1000}
            step={50}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Hotel Class</InputLabel>
            <Select
              multiple
              value={filters.hotelClass}
              onChange={handleChange('hotelClass')}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={`${value} Star`} />
                  ))}
                </Box>
              )}
            >
              {[3, 4, 5].map((star) => (
                <MenuItem key={star} value={star}>
                  {star} Star
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Amenities</InputLabel>
            <Select
              multiple
              value={filters.amenities}
              onChange={handleChange('amenities')}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} />
                  ))}
                </Box>
              )}
            >
              {amenitiesList.map((amenity) => (
                <MenuItem key={amenity} value={amenity}>
                  {amenity}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            size="large"
            fullWidth
          >
            Search Hotels
          </Button>
        </Grid>
      </Grid>
    </form>
  );
};

export default SearchFilters;
