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
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  Timeline,
  Visibility,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService, { BacktestResult, BacktestSummary } from '../services/api';

interface DashboardState {
  loading: boolean;
  error: string | null;
  summary: BacktestSummary | null;
  results: BacktestResult[];
  wyckoffReport: any;
  totalSymbols: number;
  symbolsWithData: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<DashboardState>({
    loading: true,
    error: null,
    summary: null,
    results: [],
    wyckoffReport: null,
    totalSymbols: 0,
    symbolsWithData: 0,
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Check if backend is available
      const isHealthy = await apiService.healthCheck();
      if (!isHealthy) {
        throw new Error('Backend service is not available');
      }

      // Load latest backtest results, Wyckoff report, and symbol counts
      const [backtestData, wyckoffData, symbolsData, latestData] = await Promise.all([
        apiService.getLatestBacktestResults(),
        apiService.getWyckoffReport(),
        apiService.getSymbols(),
        fetch('http://localhost:5001/api/stocks/latest').then(res => res.json()),
      ]);

      setState(prev => ({
        ...prev,
        loading: false,
        summary: backtestData.summary,
        results: backtestData.results,
        wyckoffReport: wyckoffData,
        totalSymbols: symbolsData.length,
        symbolsWithData: latestData.data ? latestData.data.length : 0,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load dashboard data',
      }));
    }
  };

  const runNewBacktest = async () => {
    setState(prev => ({ ...prev, loading: true }));
    
    try {
      const backtestData = await apiService.runBacktest();
      
      setState(prev => ({
        ...prev,
        loading: false,
        summary: backtestData.summary,
        results: backtestData.results,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to run backtest',
      }));
    }
  };

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'success';
    if (value < 0) return 'error';
    return 'default';
  };

  const getPerformanceIcon = (value: number) => {
    if (value > 0) return <TrendingUp />;
    if (value < 0) return <TrendingDown />;
    return <Timeline />;
  };

  if (state.loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading dashboard...
        </Typography>
      </Box>
    );
  }

  if (state.error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {state.error}
        <Button onClick={loadDashboardData} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Wyckoff Trading Dashboard
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            onClick={() => navigate('/symbols')}
          >
            View All Symbols ({state.totalSymbols})
          </Button>
          <Button
            variant="contained"
            startIcon={<Assessment />}
            onClick={runNewBacktest}
            disabled={state.loading}
          >
            Run New Backtest
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Box display="grid" gridTemplateColumns={{ xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(5, 1fr)' }} gap={3} mb={3}>
        {/* Symbol Summary Card */}
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Symbols
            </Typography>
            <Typography variant="h4">
              {state.totalSymbols}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {state.symbolsWithData} with data
            </Typography>
          </CardContent>
        </Card>

        {/* Backtest Summary Cards */}
        {state.summary && (
          <>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Return
              </Typography>
              <Typography variant="h4" color={getPerformanceColor(state.summary.overall_return_percent || 0)}>
                {(state.summary.overall_return_percent || 0).toFixed(2)}%
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                {getPerformanceIcon(state.summary.overall_return_percent || 0)}
                <Typography variant="body2" color="textSecondary" sx={{ ml: 1 }}>
                  ${(state.summary.total_final_value || 0).toLocaleString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Trades
              </Typography>
              <Typography variant="h4">
                {(state.results || []).reduce((sum, r) => sum + (r.performance_metrics?.total_trades || 0), 0)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Across {state.summary.total_symbols || 0} symbols
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Win Rate
              </Typography>
              <Typography variant="h4">
                {(state.results || []).length > 0 
                  ? ((state.results || []).reduce((sum, r) => sum + (r.performance_metrics?.win_rate || 0), 0) / (state.results || []).length).toFixed(1)
                  : 0}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Average across all symbols
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Max Drawdown
              </Typography>
              <Typography variant="h4" color="error">
                {(state.results || []).length > 0
                  ? Math.max(...(state.results || []).map(r => r.performance_metrics?.max_drawdown_percent || 0)).toFixed(1)
                  : 0}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Worst performing symbol
              </Typography>
            </CardContent>
          </Card>
          </>
        )}
      </Box>

      {/* Top Performers */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Top Performers
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Symbol</TableCell>
                  <TableCell align="right">Return</TableCell>
                  <TableCell align="right">Trades</TableCell>
                  <TableCell align="right">Win Rate</TableCell>
                  <TableCell align="right">Sharpe Ratio</TableCell>
                  <TableCell align="right">Max Drawdown</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(state.results || [])
                  .sort((a, b) => (b.performance_metrics?.total_return_percent || 0) - (a.performance_metrics?.total_return_percent || 0))
                  .slice(0, 5)
                  .map((result) => (
                    <TableRow key={result.symbol} hover>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {result.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${(result.performance_metrics?.total_return_percent || 0).toFixed(2)}%`}
                          color={getPerformanceColor(result.performance_metrics?.total_return_percent || 0)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        {result.performance_metrics?.total_trades || 0}
                      </TableCell>
                      <TableCell align="right">
                        {(result.performance_metrics?.win_rate || 0).toFixed(1)}%
                      </TableCell>
                      <TableCell align="right">
                        {(result.performance_metrics?.sharpe_ratio || 0).toFixed(2)}
                      </TableCell>
                      <TableCell align="right">
                        <Typography color="error">
                          {(result.performance_metrics?.max_drawdown_percent || 0).toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Chart">
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/chart/${result.symbol}`)}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Wyckoff Phase Summary */}
      {state.wyckoffReport && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Wyckoff Analysis
            </Typography>
            <Box display="grid" gridTemplateColumns={{ xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }} gap={2}>
              {(state.wyckoffReport?.analysis_results || []).slice(0, 6).map((analysis: any) => (
                <Box
                  key={analysis.symbol}
                  sx={{
                    p: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="subtitle2" fontWeight="bold">
                    {analysis.symbol}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Phase: {analysis.current_phase || 'Unknown'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Score: {analysis.wyckoff_score || 0}/100
                  </Typography>
                  <Chip
                    label={analysis.signal || 'HOLD'}
                    color={analysis.signal === 'BUY' ? 'success' : analysis.signal === 'SELL' ? 'error' : 'default'}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Dashboard;