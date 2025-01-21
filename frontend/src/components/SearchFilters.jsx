import React from 'react';
import {
  Box,
  Card,
  Grid,
  TextField,
  Button,
  Chip,
  Typography,
  Slider,
  useTheme,
  InputAdornment,
  Tooltip,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import {
  Search as SearchIcon,
  LocationOn as LocationIcon,
  Person as PersonIcon,
  Hotel as HotelIcon,
  AttachMoney as MoneyIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

const amenities = [
  { label: 'Pool', icon: '🏊‍♂️' },
  { label: 'WiFi', icon: '📶' },
  { label: 'Restaurant', icon: '🍽️' },
  { label: 'Parking', icon: '🅿️' },
  { label: 'Spa', icon: '💆‍♂️' },
  { label: 'Gym', icon: '💪' },
  { label: 'Bar', icon: '🍸' },
  { label: 'Room Service', icon: '🛎️' },
];

function SearchFilters({ searchParams, setSearchParams, onSearch, loading }) {
  const theme = useTheme();

  const handleAmenityToggle = (amenity) => {
    setSearchParams((prev) => ({
      ...prev,
      selectedAmenities: prev.selectedAmenities.includes(amenity)
        ? prev.selectedAmenities.filter((a) => a !== amenity)
        : [...prev.selectedAmenities, amenity],
    }));
  };

  return (
    <Card sx={{ p: 3, mb: 4 }}>
      <Grid container spacing={3}>
        {/* Location Search */}
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="City or Location"
            value={searchParams.city}
            onChange={(e) =>
              setSearchParams((prev) => ({ ...prev, city: e.target.value }))
            }
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LocationIcon color="primary" />
                </InputAdornment>
              ),
            }}
            placeholder="Enter city name"
          />
        </Grid>

        {/* Date Selection */}
        <Grid item xs={12} md={4}>
          <DatePicker
            label="Check-in Date"
            value={searchParams.checkIn}
            onChange={(date) =>
              setSearchParams((prev) => ({ ...prev, checkIn: date }))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                fullWidth
                InputProps={{
                  ...params.InputProps,
                  startAdornment: (
                    <InputAdornment position="start">
                      {params.InputProps.startAdornment}
                    </InputAdornment>
                  ),
                }}
              />
            )}
          />
        </Grid>

        <Grid item xs={12} md={4}>
          <DatePicker
            label="Check-out Date"
            value={searchParams.checkOut}
            onChange={(date) =>
              setSearchParams((prev) => ({ ...prev, checkOut: date }))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                fullWidth
                InputProps={{
                  ...params.InputProps,
                  startAdornment: (
                    <InputAdornment position="start">
                      {params.InputProps.startAdornment}
                    </InputAdornment>
                  ),
                }}
              />
            )}
          />
        </Grid>

        {/* Guests and Rooms */}
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            type="number"
            label="Number of Guests"
            value={searchParams.guests}
            onChange={(e) =>
              setSearchParams((prev) => ({
                ...prev,
                guests: parseInt(e.target.value),
              }))
            }
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <PersonIcon color="primary" />
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            type="number"
            label="Number of Rooms"
            value={searchParams.rooms}
            onChange={(e) =>
              setSearchParams((prev) => ({
                ...prev,
                rooms: parseInt(e.target.value),
              }))
            }
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <HotelIcon color="primary" />
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        {/* Price Range */}
        <Grid item xs={12}>
          <Box sx={{ px: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <MoneyIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="subtitle1">Price Range</Typography>
              <Tooltip title="Drag the sliders to set your preferred price range">
                <InfoIcon sx={{ ml: 1, color: 'text.secondary' }} />
              </Tooltip>
            </Box>
            <Slider
              value={searchParams.priceRange}
              onChange={(e, newValue) =>
                setSearchParams((prev) => ({
                  ...prev,
                  priceRange: newValue,
                }))
              }
              valueLabelDisplay="auto"
              min={0}
              max={1000}
              step={50}
              marks={[
                { value: 0, label: '$0' },
                { value: 250, label: '$250' },
                { value: 500, label: '$500' },
                { value: 750, label: '$750' },
                { value: 1000, label: '$1000' },
              ]}
              sx={{
                '& .MuiSlider-thumb': {
                  height: 24,
                  width: 24,
                  '&:hover': {
                    boxShadow: `0 0 0 8px ${theme.palette.primary.main}20`,
                  },
                },
              }}
            />
          </Box>
        </Grid>

        {/* Amenities */}
        <Grid item xs={12}>
          <Typography variant="subtitle1" sx={{ mb: 2 }}>
            Amenities
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {amenities.map((amenity) => (
              <Chip
                key={amenity.label}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <span>{amenity.icon}</span>
                    <span>{amenity.label}</span>
                  </Box>
                }
                onClick={() => handleAmenityToggle(amenity.label)}
                color={
                  searchParams.selectedAmenities.includes(amenity.label)
                    ? 'primary'
                    : 'default'
                }
                variant={
                  searchParams.selectedAmenities.includes(amenity.label)
                    ? 'filled'
                    : 'outlined'
                }
                sx={{
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                  },
                }}
              />
            ))}
          </Box>
        </Grid>

        {/* Search Button */}
        <Grid item xs={12}>
          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={onSearch}
            disabled={loading}
            startIcon={<SearchIcon />}
            sx={{
              py: 1.5,
              fontSize: '1.1rem',
              '&:hover': {
                transform: 'translateY(-2px)',
              },
            }}
          >
            {loading ? 'Searching...' : 'Search Hotels'}
          </Button>
        </Grid>
      </Grid>
    </Card>
  );
}

export default SearchFilters;
