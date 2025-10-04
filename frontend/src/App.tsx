import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, Container, Button } from '@mui/material';
import Dashboard from './components/Dashboard';
import BacktestViewer from './components/BacktestViewer';
import ChartViewer from './components/ChartViewer';
import StockSymbolsViewer from './components/StockSymbolsViewer';
import StopLossOptimizer from './components/StopLossOptimizer';
import EMATrading from './components/EMATrading';
import EMAChart from './components/EMAChart';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
  },
});

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            KyzerEye Stock Labs - Wyckoff Trading Platform
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              color="inherit"
              onClick={() => navigate('/')}
              variant={location.pathname === '/' ? 'outlined' : 'text'}
            >
              Dashboard
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/symbols')}
              variant={location.pathname === '/symbols' ? 'outlined' : 'text'}
            >
              Symbols
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/backtest')}
              variant={location.pathname === '/backtest' ? 'outlined' : 'text'}
            >
              Backtest
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/stop-loss')}
              variant={location.pathname === '/stop-loss' ? 'outlined' : 'text'}
            >
              Stop Loss
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/ema-trading')}
              variant={location.pathname === '/ema-trading' ? 'outlined' : 'text'}
            >
              EMA Trading
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/ema-chart')}
              variant={location.pathname === '/ema-chart' ? 'outlined' : 'text'}
            >
              EMA Chart
            </Button>
          </Box>
        </Toolbar>
      </AppBar>
          
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/symbols" element={<StockSymbolsViewer />} />
          <Route path="/backtest" element={<BacktestViewer />} />
            <Route path="/stop-loss" element={<StopLossOptimizer />} />
            <Route path="/ema-trading" element={<EMATrading />} />
            <Route path="/ema-chart" element={<EMAChart />} />
          <Route path="/chart/:symbol" element={<ChartViewer />} />
        </Routes>
      </Container>
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  );
}

export default App;