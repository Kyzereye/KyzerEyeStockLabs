import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  Timeline,
  ExpandMore
} from '@mui/icons-material';
import { apiService } from '../services/api';

interface StopLossResult {
  period_start: string;
  period_end: string;
  optimal_stop_loss: number;
  total_return: number;
  win_rate: number;
  max_drawdown: number;
  sharpe_ratio: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  trades: any[];
}

interface StopLossOptimization {
  symbol: string;
  analysis_date: string;
  overall_optimal: number;
  stop_loss_range: [number, number];
  test_intervals: number[];
  monthly_results: StopLossResult[];
  quarterly_results: StopLossResult[];
  yearly_results: StopLossResult[];
}

interface StopLossSummary {
  symbol: string;
  analysis_date: string;
  overall_optimal: number;
  statistics: {
    monthly: {
      count: number;
      min: number;
      max: number;
      avg: number;
      median: number;
    };
    quarterly: {
      count: number;
      min: number;
      max: number;
      avg: number;
      median: number;
    };
    yearly: {
      count: number;
      min: number;
      max: number;
      avg: number;
      median: number;
    };
  };
  recommendations: {
    conservative: number;
    moderate: number;
    aggressive: number;
  };
}

const StopLossOptimizer: React.FC = () => {
  const [symbol, setSymbol] = useState('');
  const [initialCapital, setInitialCapital] = useState(100000);
  const [optimization, setOptimization] = useState<StopLossOptimization | null>(null);
  const [summary, setSummary] = useState<StopLossSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  const loadOptimization = async () => {
    if (!symbol.trim()) {
      setError('Please enter a symbol');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:5001/api/stop-loss/optimize/${symbol.toUpperCase()}?initial_capital=${initialCapital}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setOptimization(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    if (!symbol.trim()) {
      setError('Please enter a symbol');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:5001/api/stop-loss/summary/${symbol.toUpperCase()}?initial_capital=${initialCapital}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

  const getPerformanceColor = (value: number, isPositive: boolean = true) => {
    if (isPositive) {
      return value > 0 ? 'success' : 'error';
    }
    return value < 0 ? 'success' : 'error';
  };

  const renderResultsTable = (results: StopLossResult[], title: string) => (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title} ({results.length} periods)
        </Typography>
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Period</TableCell>
                <TableCell align="right">Optimal Stop Loss</TableCell>
                <TableCell align="right">Total Return</TableCell>
                <TableCell align="right">Win Rate</TableCell>
                <TableCell align="right">Max Drawdown</TableCell>
                <TableCell align="right">Sharpe Ratio</TableCell>
                <TableCell align="right">Trades</TableCell>
                <TableCell align="right">Profit Factor</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {results.map((result, index) => (
                <TableRow key={index}>
                  <TableCell>
                    {new Date(result.period_start).toLocaleDateString()} - {new Date(result.period_end).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <Chip 
                      label={formatPercentage(result.optimal_stop_loss)} 
                      color="primary" 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Chip 
                      label={`${result.total_return.toFixed(1)}%`} 
                      color={getPerformanceColor(result.total_return) as any} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Chip 
                      label={`${result.win_rate.toFixed(1)}%`} 
                      color={result.win_rate > 50 ? 'success' : 'error'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Chip 
                      label={`${result.max_drawdown.toFixed(1)}%`} 
                      color={result.max_drawdown < 10 ? 'success' : 'error'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell align="right">
                    {result.sharpe_ratio.toFixed(2)}
                  </TableCell>
                  <TableCell align="right">
                    {result.total_trades}
                  </TableCell>
                  <TableCell align="right">
                    {result.profit_factor.toFixed(2)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );

  const renderSummaryStats = () => {
    if (!summary) return null;

    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Stop Loss Statistics Summary
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" color="primary">
                    Monthly Analysis
                  </Typography>
                  <Typography variant="body2">
                    Count: {summary.statistics.monthly.count}
                  </Typography>
                  <Typography variant="body2">
                    Range: {formatPercentage(summary.statistics.monthly.min)} - {formatPercentage(summary.statistics.monthly.max)}
                  </Typography>
                  <Typography variant="body2">
                    Average: {formatPercentage(summary.statistics.monthly.avg)}
                  </Typography>
                  <Typography variant="body2">
                    Median: {formatPercentage(summary.statistics.monthly.median)}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" color="primary">
                    Quarterly Analysis
                  </Typography>
                  <Typography variant="body2">
                    Count: {summary.statistics.quarterly.count}
                  </Typography>
                  <Typography variant="body2">
                    Range: {formatPercentage(summary.statistics.quarterly.min)} - {formatPercentage(summary.statistics.quarterly.max)}
                  </Typography>
                  <Typography variant="body2">
                    Average: {formatPercentage(summary.statistics.quarterly.avg)}
                  </Typography>
                  <Typography variant="body2">
                    Median: {formatPercentage(summary.statistics.quarterly.median)}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" color="primary">
                    Yearly Analysis
                  </Typography>
                  <Typography variant="body2">
                    Count: {summary.statistics.yearly.count}
                  </Typography>
                  <Typography variant="body2">
                    Range: {formatPercentage(summary.statistics.yearly.min)} - {formatPercentage(summary.statistics.yearly.max)}
                  </Typography>
                  <Typography variant="body2">
                    Average: {formatPercentage(summary.statistics.yearly.avg)}
                  </Typography>
                  <Typography variant="body2">
                    Median: {formatPercentage(summary.statistics.yearly.median)}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Box>
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recommended Stop Loss Levels
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText' }}>
                  <CardContent>
                    <Typography variant="h6">Conservative</Typography>
                    <Typography variant="h4">
                      {formatPercentage(summary.recommendations.conservative)}
                    </Typography>
                    <Typography variant="body2">
                      Lower risk, tighter stops
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Card sx={{ bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                  <CardContent>
                    <Typography variant="h6">Moderate</Typography>
                    <Typography variant="h4">
                      {formatPercentage(summary.recommendations.moderate)}
                    </Typography>
                    <Typography variant="body2">
                      Balanced approach
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Card sx={{ bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                  <CardContent>
                    <Typography variant="h6">Aggressive</Typography>
                    <Typography variant="h4">
                      {formatPercentage(summary.recommendations.aggressive)}
                    </Typography>
                    <Typography variant="body2">
                      Higher risk tolerance
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Stop Loss Optimization
      </Typography>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Stock Symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="e.g., AAPL"
              />
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Initial Capital"
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
              />
            </Box>
            <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  onClick={loadOptimization}
                  disabled={loading}
                  startIcon={<Assessment />}
                >
                  Run Full Analysis
                </Button>
                <Button
                  variant="outlined"
                  onClick={loadSummary}
                  disabled={loading}
                  startIcon={<Timeline />}
                >
                  Quick Summary
                </Button>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {optimization && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                {optimization.symbol} - Stop Loss Optimization Results
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Analysis Date: {new Date(optimization.analysis_date).toLocaleString()}
              </Typography>
              <Typography variant="h6" color="primary">
                Overall Optimal Stop Loss: {formatPercentage(optimization.overall_optimal)}
              </Typography>
            </CardContent>
          </Card>

          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 2 }}>
            <Tab label="Monthly Results" />
            <Tab label="Quarterly Results" />
            <Tab label="Yearly Results" />
          </Tabs>

          {activeTab === 0 && renderResultsTable(optimization.monthly_results, 'Monthly Optimization Results')}
          {activeTab === 1 && renderResultsTable(optimization.quarterly_results, 'Quarterly Optimization Results')}
          {activeTab === 2 && renderResultsTable(optimization.yearly_results, 'Yearly Optimization Results')}
        </Box>
      )}

      {summary && renderSummaryStats()}
    </Box>
  );
};

export default StopLossOptimizer;
