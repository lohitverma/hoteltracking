import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Rating,
  Button,
  Chip,
  Box,
  CircularProgress,
  Typography,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

const HotelPriceTable = ({ hotels = [], loading }) => {
  const navigate = useNavigate();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!hotels.length) {
    return (
      <Box sx={{ textAlign: 'center', p: 3 }}>
        <Typography variant="body1" color="text.secondary">
          No hotels found. Try adjusting your search criteria.
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table sx={{ minWidth: 650 }} aria-label="hotel price table">
        <TableHead>
          <TableRow>
            <TableCell>Hotel Name</TableCell>
            <TableCell align="center">Rating</TableCell>
            <TableCell align="center">Price</TableCell>
            <TableCell align="center">Location</TableCell>
            <TableCell align="center">Amenities</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {hotels.map((hotel) => (
            <TableRow
              key={hotel.id}
              sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
            >
              <TableCell component="th" scope="row">
                {hotel.name}
              </TableCell>
              <TableCell align="center">
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <Rating value={hotel.rating} precision={0.5} readOnly />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                    ({hotel.rating})
                  </Typography>
                </Box>
              </TableCell>
              <TableCell align="center">
                <Typography variant="h6" color="primary">
                  ${hotel.price}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  per night
                </Typography>
              </TableCell>
              <TableCell align="center">{hotel.location}</TableCell>
              <TableCell align="center">
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', justifyContent: 'center' }}>
                  {hotel.amenities.slice(0, 3).map((amenity) => (
                    <Chip
                      key={amenity}
                      label={amenity}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                  {hotel.amenities.length > 3 && (
                    <Chip
                      label={`+${hotel.amenities.length - 3} more`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>
              </TableCell>
              <TableCell align="center">
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => navigate(`/hotel/${hotel.id}`)}
                >
                  View Details
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default HotelPriceTable;
