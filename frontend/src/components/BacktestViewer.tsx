import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  ExpandMore,
  Assessment,
  TrendingUp,
  TrendingDown,
  Timeline,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService, { BacktestResult, BacktestSummary, Trade } from '../services/api';

interface BacktestViewerState {
  loading: boolean;
  error: string | null;
  summary: BacktestSummary | null;
  results: BacktestResult[];
  selectedSymbol: string;
  availableReports: Array<{
    filename: string;
    created: string;
    size: number;
  }>;
}

const BacktestViewer: React.FC = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<BacktestViewerState>({
    loading: true,
    error: null,
    summary: null,
    results: [],
    selectedSymbol: '',
    availableReports: [],
  });

  useEffect(() => {
    loadAvailableReports();
  }, []);

  const loadAvailableReports = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const reports = await apiService.getAvailableReports();
      
      if (reports.length > 0) {
        // Load the most recent report
        const latestReport = await apiService.getReport(reports[0].filename);
        
        setState(prev => ({
          ...prev,
          loading: false,
          summary: latestReport.summary,
          results: latestReport.results,
          availableReports: reports,
        }));
      } else {
        setState(prev => ({
          ...prev,
          loading: false,
          error: 'No backtest reports available. Run a backtest first.',
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load backtest reports',
      }));
    }
  };

  const loadReport = async (filename: string) => {
    setState(prev => ({ ...prev, loading: true }));

    try {
      const report = await apiService.getReport(filename);
      
      setState(prev => ({
        ...prev,
        loading: false,
        summary: report.summary,
        results: report.results,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load report',
      }));
    }
  };

  const runNewBacktest = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const backtestData = await apiService.runBacktest();
      
      setState(prev => ({
        ...prev,
        loading: false,
        summary: backtestData.summary,
        results: backtestData.results,
      }));
      
      // Refresh available reports
      loadAvailableReports();
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  if (state.loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading backtest data...
        </Typography>
      </Box>
    );
  }

  if (state.error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {state.error}
        <Button onClick={loadAvailableReports} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  const selectedResult = state.selectedSymbol 
    ? state.results.find(r => r.symbol === state.selectedSymbol)
    : null;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Backtest Results Viewer
        </Typography>
        <Box>
          <Button
            variant="contained"
            startIcon={<Assessment />}
            onClick={runNewBacktest}
            disabled={state.loading}
            sx={{ mr: 2 }}
          >
            Run New Backtest
          </Button>
        </Box>
      </Box>

      {/* Report Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Available Reports
          </Typography>
          <Box display="flex" gap={2} alignItems="center">
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Select Report</InputLabel>
              <Select
                value=""
                onChange={(e) => loadReport(e.target.value)}
                label="Select Report"
              >
                {state.availableReports.map((report) => (
                  <MenuItem key={report.filename} value={report.filename}>
                    {report.filename.replace('wyckoff_backtest_report_', '').replace('.json', '')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Summary */}
      {state.summary && (
        <Box display="grid" gridTemplateColumns={{ xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }} gap={3} mb={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Overall Return
              </Typography>
              <Typography variant="h4" color={getPerformanceColor(state.summary.overall_return_percent)}>
                {state.summary.overall_return_percent.toFixed(2)}%
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                {getPerformanceIcon(state.summary.overall_return_percent)}
                <Typography variant="body2" color="textSecondary" sx={{ ml: 1 }}>
                  {formatCurrency(state.summary.total_final_value)}
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
                {state.results.reduce((sum, r) => sum + r.performance_metrics.total_trades, 0)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Across {state.summary.total_symbols} symbols
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Win Rate
              </Typography>
              <Typography variant="h4">
                {state.results.length > 0 
                  ? (state.results.reduce((sum, r) => sum + r.performance_metrics.win_rate, 0) / state.results.length).toFixed(1)
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
                {state.results.length > 0
                  ? Math.max(...state.results.map(r => r.performance_metrics.max_drawdown_percent)).toFixed(1)
                  : 0}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Worst performing symbol
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Symbol Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Detailed Analysis
          </Typography>
          <FormControl fullWidth>
            <InputLabel>Select Symbol</InputLabel>
            <Select
              value={state.selectedSymbol}
              onChange={(e) => setState(prev => ({ ...prev, selectedSymbol: e.target.value }))}
              label="Select Symbol"
            >
              {state.results.map((result) => (
                <MenuItem key={result.symbol} value={result.symbol}>
                  {result.symbol} - {result.performance_metrics.total_return_percent.toFixed(2)}% return
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </CardContent>
      </Card>

      {/* Selected Symbol Details */}
      {selectedResult && (
        <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={3}>
          {/* Performance Metrics */}
          <Box flex={1}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Metrics - {selectedResult.symbol}
                </Typography>
                <Box display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={2}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Total Return
                    </Typography>
                    <Typography variant="h6" color={getPerformanceColor(selectedResult.performance_metrics.total_return_percent)}>
                      {selectedResult.performance_metrics.total_return_percent.toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Final Value
                    </Typography>
                    <Typography variant="h6">
                      {formatCurrency(selectedResult.performance_metrics.final_value)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Win Rate
                    </Typography>
                    <Typography variant="h6">
                      {selectedResult.performance_metrics.win_rate.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Sharpe Ratio
                    </Typography>
                    <Typography variant="h6">
                      {selectedResult.performance_metrics.sharpe_ratio.toFixed(2)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Max Drawdown
                    </Typography>
                    <Typography variant="h6" color="error">
                      {selectedResult.performance_metrics.max_drawdown_percent.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Profit Factor
                    </Typography>
                    <Typography variant="h6">
                      {selectedResult.performance_metrics.profit_factor.toFixed(2)}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Phase Analysis */}
          <Box flex={1}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Wyckoff Phase Analysis
                </Typography>
                {Object.entries(selectedResult.phase_analysis.phase_counts).map(([phase, count]) => (
                  <Box key={phase} display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">{phase}</Typography>
                    <Typography variant="body2" fontWeight="bold">{count}</Typography>
                  </Box>
                ))}
                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  Total Signals: {selectedResult.phase_analysis.total_signals}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}

      {/* Trades */}
      {selectedResult && (
        <Box mt={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Trade History - {selectedResult.symbol}
              </Typography>
              <List>
                {selectedResult.trades.map((trade, index) => (
                  <Accordion key={index}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
                        <Typography variant="subtitle1">
                          {formatDate(trade.entry_date)} - {trade.exit_date ? formatDate(trade.exit_date) : 'Open'}
                        </Typography>
                        <Box display="flex" gap={1}>
                          <Typography variant="body2" color={trade.action === 'BUY' ? 'success.main' : 'error.main'}>
                            {trade.action}
                          </Typography>
                          {trade.pnl_percent && (
                            <Typography variant="body2" color={trade.pnl_percent > 0 ? 'success.main' : 'error.main'}>
                              {trade.pnl_percent > 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={2}>
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Entry Price
                          </Typography>
                          <Typography variant="body1">
                            {formatCurrency(trade.entry_price)}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Exit Price
                          </Typography>
                          <Typography variant="body1">
                            {trade.exit_price ? formatCurrency(trade.exit_price) : 'Open'}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            P&L
                          </Typography>
                          <Typography variant="body1" color={trade.pnl && trade.pnl > 0 ? 'success.main' : 'error.main'}>
                            {trade.pnl ? formatCurrency(trade.pnl) : 'Open'}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Duration
                          </Typography>
                          <Typography variant="body1">
                            {trade.duration_days ? `${trade.duration_days} days` : 'Open'}
                          </Typography>
                        </Box>
                        <Box gridColumn="1 / -1">
                          <Typography variant="body2" color="textSecondary">
                            Entry Reasoning
                          </Typography>
                          <Typography variant="body2">
                            {trade.entry_reasoning}
                          </Typography>
                        </Box>
                        {trade.exit_reasoning && (
                          <Box gridColumn="1 / -1">
                            <Typography variant="body2" color="textSecondary">
                              Exit Reasoning
                            </Typography>
                            <Typography variant="body2">
                              {trade.exit_reasoning}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </List>
            </CardContent>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default BacktestViewer;