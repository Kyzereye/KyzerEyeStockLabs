import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Grid,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Divider,
  LinearProgress
} from '@mui/material';
import { apiService } from '../services/api';

interface EMASignal {
  date: string;
  signal_type: 'BUY' | 'SELL';
  price: number;
  ema_21: number;
  ema_50: number;
  reasoning: string;
  confidence: number;
}

interface EMATrade {
  entry_date: string;
  exit_date: string | null;
  entry_price: number;
  exit_price: number | null;
  entry_signal: string;
  exit_signal: string;
  shares: number;
  pnl: number | null;
  pnl_percent: number | null;
  duration_days: number | null;
}

interface EMAPerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  total_return_percent: number;
  avg_trade_duration: number;
  max_drawdown: number;
  sharpe_ratio: number;
}

interface EMAResults {
  symbol: string;
  start_date: string;
  end_date: string;
  total_days: number;
  performance_metrics: EMAPerformanceMetrics;
  trades: EMATrade[];
  signals: EMASignal[];
  equity_curve: Array<{ date: string; equity: number }>;
}

const EMATrading: React.FC = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [initialCapital, setInitialCapital] = useState(100000);
  const [days, setDays] = useState(365);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<EMAResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  const runEMAAnalysis = async () => {
    if (!symbol.trim()) {
      setError('Please enter a stock symbol');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(
        `http://localhost:5001/api/ema/analyze/${symbol.toUpperCase()}?initial_capital=${initialCapital}&days=${days}`
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to analyze EMA trading');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signalType: string) => {
    return signalType === 'BUY' ? 'success' : 'error';
  };

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'success';
    if (value < 0) return 'error';
    return 'default';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        EMA Trading System
      </Typography>
      
      <Typography variant="subtitle1" color="textSecondary" sx={{ mb: 3 }}>
        Simple EMA Strategy: BUY when price closes above 50 EMA, SELL when price closes below 21 EMA
      </Typography>

      {/* Input Controls */}
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
                inputProps={{ min: 1000, step: 1000 }}
              />
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Days to Analyze"
                type="number"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                inputProps={{ min: 50, max: 2000 }}
              />
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <Button
                variant="contained"
                onClick={runEMAAnalysis}
                disabled={loading}
                fullWidth
                sx={{ height: '56px' }}
              >
                {loading ? <CircularProgress size={24} /> : 'Run EMA Analysis'}
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {results && (
        <Box>
          {/* Performance Summary */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Summary - {results.symbol}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Period: {new Date(results.start_date).toLocaleDateString()} to {new Date(results.end_date).toLocaleDateString()} 
                ({results.total_days} days)
              </Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                  <Typography variant="h4" color={getPerformanceColor(results.performance_metrics.total_return_percent)}>
                    {formatPercent(results.performance_metrics.total_return_percent)}
                  </Typography>
                  <Typography variant="caption">Total Return</Typography>
                </Box>
                <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                  <Typography variant="h4" color={getPerformanceColor(results.performance_metrics.total_pnl)}>
                    {formatCurrency(results.performance_metrics.total_pnl)}
                  </Typography>
                  <Typography variant="caption">Total P&L</Typography>
                </Box>
                <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                  <Typography variant="h4">
                    {results.performance_metrics.total_trades}
                  </Typography>
                  <Typography variant="caption">Total Trades</Typography>
                </Box>
                <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                  <Typography variant="h4" color={getPerformanceColor(results.performance_metrics.win_rate - 50)}>
                    {formatPercent(results.performance_metrics.win_rate)}
                  </Typography>
                  <Typography variant="caption">Win Rate</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Tabs for different views */}
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
                <Tab label="Trades" />
                <Tab label="Signals" />
                <Tab label="Performance Details" />
              </Tabs>
            </Box>

            <CardContent>
              {/* Trades Tab */}
              {activeTab === 0 && (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Entry Date</TableCell>
                        <TableCell>Exit Date</TableCell>
                        <TableCell>Entry Price</TableCell>
                        <TableCell>Exit Price</TableCell>
                        <TableCell>Shares</TableCell>
                        <TableCell>P&L</TableCell>
                        <TableCell>P&L %</TableCell>
                        <TableCell>Duration</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.trades.map((trade, index) => (
                        <TableRow key={index}>
                          <TableCell>{new Date(trade.entry_date).toLocaleDateString()}</TableCell>
                          <TableCell>
                            {trade.exit_date ? new Date(trade.exit_date).toLocaleDateString() : 'Open'}
                          </TableCell>
                          <TableCell>{formatCurrency(trade.entry_price)}</TableCell>
                          <TableCell>
                            {trade.exit_price ? formatCurrency(trade.exit_price) : 'Open'}
                          </TableCell>
                          <TableCell>{trade.shares.toLocaleString()}</TableCell>
                          <TableCell>
                            {trade.pnl ? (
                              <Chip
                                label={formatCurrency(trade.pnl)}
                                color={getPerformanceColor(trade.pnl)}
                                size="small"
                              />
                            ) : 'Open'}
                          </TableCell>
                          <TableCell>
                            {trade.pnl_percent ? (
                              <Chip
                                label={formatPercent(trade.pnl_percent)}
                                color={getPerformanceColor(trade.pnl_percent)}
                                size="small"
                              />
                            ) : 'Open'}
                          </TableCell>
                          <TableCell>
                            {trade.duration_days ? `${trade.duration_days} days` : 'Open'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {/* Signals Tab */}
              {activeTab === 1 && (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Signal</TableCell>
                        <TableCell>Price</TableCell>
                        <TableCell>EMA 21</TableCell>
                        <TableCell>EMA 50</TableCell>
                        <TableCell>Confidence</TableCell>
                        <TableCell>Reasoning</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.signals.map((signal, index) => (
                        <TableRow key={index}>
                          <TableCell>{new Date(signal.date).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Chip
                              label={signal.signal_type}
                              color={getSignalColor(signal.signal_type)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{formatCurrency(signal.price)}</TableCell>
                          <TableCell>{formatCurrency(signal.ema_21)}</TableCell>
                          <TableCell>{formatCurrency(signal.ema_50)}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <LinearProgress
                                variant="determinate"
                                value={signal.confidence * 100}
                                sx={{ width: 60, mr: 1 }}
                              />
                              <Typography variant="caption">
                                {formatPercent(signal.confidence * 100)}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>{signal.reasoning}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {/* Performance Details Tab */}
              {activeTab === 2 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 300px' }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Trading Statistics
                        </Typography>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Total Trades: <strong>{results.performance_metrics.total_trades}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Winning Trades: <strong>{results.performance_metrics.winning_trades}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Losing Trades: <strong>{results.performance_metrics.losing_trades}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Win Rate: <strong>{formatPercent(results.performance_metrics.win_rate)}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Avg Trade Duration: <strong>{results.performance_metrics.avg_trade_duration.toFixed(1)} days</strong>
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Box>
                  
                  <Box sx={{ flex: '1 1 300px' }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Risk Metrics
                        </Typography>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Max Drawdown: <strong>{formatCurrency(results.performance_metrics.max_drawdown)}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Sharpe Ratio: <strong>{results.performance_metrics.sharpe_ratio.toFixed(2)}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Initial Capital: <strong>{formatCurrency(initialCapital)}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Final Value: <strong>{formatCurrency(initialCapital + results.performance_metrics.total_pnl)}</strong>
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default EMATrading;
