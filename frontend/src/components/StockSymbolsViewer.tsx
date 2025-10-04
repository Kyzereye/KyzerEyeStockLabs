import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Refresh,
  Visibility,
  Search,
  Add,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

interface StockSymbol {
  id: number;
  symbol: string;
  company_name: string;
  market_cap: number | null;
  created_at: string;
  updated_at: string;
}

interface StockSymbolsViewerState {
  loading: boolean;
  error: string | null;
  symbols: StockSymbol[];
  filteredSymbols: StockSymbol[];
  searchTerm: string;
  latestData: any[];
  currentPage: number;
  itemsPerPage: number;
}

const StockSymbolsViewer: React.FC = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<StockSymbolsViewerState>({
    loading: true,
    error: null,
    symbols: [],
    filteredSymbols: [],
    searchTerm: '',
    latestData: [],
    currentPage: 1,
    itemsPerPage: 10,
  });

  useEffect(() => {
    loadSymbols();
  }, []);

  useEffect(() => {
    // Filter symbols based on search term
    const filtered = state.symbols.filter(symbol =>
      symbol.symbol.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
      symbol.company_name.toLowerCase().includes(state.searchTerm.toLowerCase())
    );
    setState(prev => ({ ...prev, filteredSymbols: filtered, currentPage: 1 }));
  }, [state.symbols, state.searchTerm]);

  const loadSymbols = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [symbolsResponse, latestDataResponse] = await Promise.all([
        apiService.getSymbols(),
        fetch('http://localhost:5001/api/stocks/latest').then(res => res.json()),
      ]);

      // Transform the symbols response to match our interface
      const symbolsData = symbolsResponse.map((symbol: any) => ({
        id: symbol.id,
        symbol: symbol.symbol,
        company_name: symbol.company_name,
        market_cap: symbol.market_cap,
        created_at: symbol.created_at,
        updated_at: symbol.updated_at,
      }));

      setState(prev => ({
        ...prev,
        loading: false,
        symbols: symbolsData,
        filteredSymbols: symbolsData,
        latestData: latestDataResponse.data || [],
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load stock symbols',
      }));
    }
  };

  const getSymbolLatestData = (symbol: string) => {
    return state.latestData.find(data => data.symbol === symbol);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Pagination helpers
  const getTotalPages = () => {
    return Math.ceil(state.filteredSymbols.length / state.itemsPerPage);
  };

  const getCurrentPageSymbols = () => {
    const startIndex = (state.currentPage - 1) * state.itemsPerPage;
    const endIndex = startIndex + state.itemsPerPage;
    return state.filteredSymbols.slice(startIndex, endIndex);
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setState(prev => ({ ...prev, currentPage: page }));
  };

  const handleItemsPerPageChange = (event: any) => {
    setState(prev => ({ 
      ...prev, 
      itemsPerPage: event.target.value,
      currentPage: 1 
    }));
  };

  const fetchDataForSymbol = async (symbol: string) => {
    try {
      const response = await fetch(`http://localhost:5001/api/stocks/${symbol}/fetch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ period: '1y' }),
      });
      
      if (response.ok) {
        // Refresh the symbols to get updated data
        loadSymbols();
      }
    } catch (error) {
      console.error(`Failed to fetch data for ${symbol}:`, error);
    }
  };

  const fetchDataForAllSymbols = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/stocks/fetch-all', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ period: '1y', delay: 1.0 }),
      });
      
      if (response.ok) {
        // Refresh the symbols to get updated data
        setTimeout(() => loadSymbols(), 2000); // Wait 2 seconds for data to be processed
      }
    } catch (error) {
      console.error('Failed to fetch data for all symbols:', error);
    }
  };

  if (state.loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading stock symbols...
        </Typography>
      </Box>
    );
  }

  if (state.error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {state.error}
        <Button onClick={loadSymbols} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Stock Symbols ({state.symbols.length})
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadSymbols}
            disabled={state.loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={fetchDataForAllSymbols}
            disabled={state.loading}
          >
            Fetch Data for All
          </Button>
        </Box>
      </Box>

      {/* Search and Stats */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <TextField
              placeholder="Search symbols or company names..."
              value={state.searchTerm}
              onChange={(e) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 300 }}
            />
            <Box display="flex" gap={2}>
              <Chip
                label={`${state.symbols.length} Total Symbols`}
                color="primary"
                variant="outlined"
              />
              <Chip
                label={`${state.latestData.length} With Data`}
                color="success"
                variant="outlined"
              />
              <Chip
                label={`${state.symbols.length - state.latestData.length} No Data`}
                color="warning"
                variant="outlined"
              />
            </Box>
          </Box>
          
          {/* Pagination Controls */}
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center" gap={2}>
              <Typography variant="body2" color="textSecondary">
                Show:
              </Typography>
              <FormControl size="small" sx={{ minWidth: 80 }}>
                <Select
                  value={state.itemsPerPage}
                  onChange={handleItemsPerPageChange}
                >
                  <MenuItem value={5}>5</MenuItem>
                  <MenuItem value={10}>10</MenuItem>
                  <MenuItem value={25}>25</MenuItem>
                  <MenuItem value={50}>50</MenuItem>
                  <MenuItem value={100}>100</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="body2" color="textSecondary">
                per page
              </Typography>
            </Box>
            
            <Typography variant="body2" color="textSecondary">
              Showing {((state.currentPage - 1) * state.itemsPerPage) + 1} to {Math.min(state.currentPage * state.itemsPerPage, state.filteredSymbols.length)} of {state.filteredSymbols.length} symbols
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Symbols Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {state.searchTerm ? `Search Results (${state.filteredSymbols.length})` : 'All Stock Symbols'}
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Symbol</TableCell>
                  <TableCell>Company Name</TableCell>
                  <TableCell align="right">Latest Price</TableCell>
                  <TableCell align="right">Volume</TableCell>
                  <TableCell align="center">Data Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {getCurrentPageSymbols().map((symbol) => {
                  const latestData = getSymbolLatestData(symbol.symbol);
                  const hasData = !!latestData;
                  
                  return (
                    <TableRow key={symbol.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {symbol.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {symbol.company_name}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {hasData ? (
                          <Typography variant="body2" fontWeight="bold">
                            {formatCurrency(parseFloat(latestData.close))}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="textSecondary">
                            No data
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {hasData ? (
                          <Typography variant="body2">
                            {latestData.volume.toLocaleString()}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="textSecondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={hasData ? 'Has Data' : 'No Data'}
                          color={hasData ? 'success' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Box display="flex" gap={1}>
                          {hasData && (
                            <Tooltip title="View Chart">
                              <IconButton
                                size="small"
                                onClick={() => navigate(`/chart/${symbol.symbol}`)}
                              >
                                <Visibility />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Fetch Data">
                            <IconButton
                              size="small"
                              onClick={() => fetchDataForSymbol(symbol.symbol)}
                            >
                              <Refresh />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
          
          {state.filteredSymbols.length === 0 && (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="textSecondary">
                No symbols found matching "{state.searchTerm}"
              </Typography>
            </Box>
          )}
          
          {/* Pagination */}
          {state.filteredSymbols.length > 0 && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Pagination
                count={getTotalPages()}
                page={state.currentPage}
                onChange={handlePageChange}
                color="primary"
                size="large"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default StockSymbolsViewer;
