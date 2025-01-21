import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme.jsx';
import Layout from './components/Layout.jsx';
import Home from './pages/Home.jsx';
import HotelSearch from './pages/HotelSearch.jsx';
import HotelDetails from './pages/HotelDetails.jsx';
import PriceAlerts from './pages/PriceAlerts.jsx';
import ChatAssistant from './pages/ChatAssistant.jsx';

const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<HotelSearch />} />
            <Route path="/hotel/:id" element={<HotelDetails />} />
            <Route path="/alerts" element={<PriceAlerts />} />
            <Route path="/chat" element={<ChatAssistant />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
