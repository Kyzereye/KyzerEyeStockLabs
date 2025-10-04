import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Autocomplete
} from '@mui/material';
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData, Time } from 'lightweight-charts';

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

interface StockData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

const EMAChart: React.FC = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [days, setDays] = useState(0); // 0 means all available data
  const [atrPeriod, setAtrPeriod] = useState(14);
  const [atrMultiplier, setAtrMultiplier] = useState(2.0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stockData, setStockData] = useState<StockData[]>([]);
  const [emaResults, setEmaResults] = useState<EMAResults | null>(null);
  const [timeframe, setTimeframe] = useState('all');
  const [availableSymbols, setAvailableSymbols] = useState<string[]>([]);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  // Signal markers are now handled directly on the candlestick series

  // Fetch available symbols on component mount
  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/stocks/');
        if (response.ok) {
          const data = await response.json();
          const symbols = data.data ? data.data.map((item: any) => item.symbol) : [];
          setAvailableSymbols(symbols);
        }
      } catch (error) {
        console.error('Error fetching symbols:', error);
      }
    };
    
    fetchSymbols();
  }, []);

  const loadData = async () => {
    if (!symbol.trim()) {
      setError('Please enter a stock symbol');
      return;
    }

    setLoading(true);
    setError(null);
    setStockData([]);
    setEmaResults(null);

    try {
      // Load stock data with EMA
      const stockResponse = await fetch(
        `http://localhost:5001/api/stocks/${symbol.toUpperCase()}?days=${days}&include_ema=true`
      );
      
      if (!stockResponse.ok) {
        const errorData = await stockResponse.json();
        throw new Error(errorData.error || 'Failed to load stock data');
      }

      const stockResponseData = await stockResponse.json();
      console.log('Stock data loaded:', stockResponseData.data?.length || 0, 'records');
      setStockData(stockResponseData.data || []);

      // Load EMA analysis
        const emaResponse = await fetch(
          `http://localhost:5001/api/ema/analyze`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              symbol: symbol.toUpperCase(),
              initial_capital: 100000,
              days: days,
              atr_period: atrPeriod,
              atr_multiplier: atrMultiplier
            })
          }
        );
      
      if (!emaResponse.ok) {
        const errorData = await emaResponse.json();
        throw new Error(errorData.error || 'Failed to load EMA analysis');
      }

      const emaData = await emaResponse.json();
      console.log('EMA data loaded:', emaData);
      setEmaResults(emaData);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const filterDataByTimeframe = (data: any[], timeframe: string) => {
    if (timeframe === 'all') return data;
    
    const now = new Date();
    const cutoffDate = new Date();
    
    switch (timeframe) {
      case '1m':
        cutoffDate.setMonth(now.getMonth() - 1);
        break;
      case '3m':
        cutoffDate.setMonth(now.getMonth() - 3);
        break;
      case '6m':
        cutoffDate.setMonth(now.getMonth() - 6);
        break;
      case '1y':
        cutoffDate.setFullYear(now.getFullYear() - 1);
        break;
      case '2y':
        cutoffDate.setFullYear(now.getFullYear() - 2);
        break;
      default:
        return data;
    }
    
    return data.filter(item => new Date(item.date) >= cutoffDate);
  };

  const initializeChart = () => {
    if (!chartContainerRef.current || chartRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#1e1e1e' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#485158',
      },
      timeScale: {
        borderColor: '#485158',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    chartRef.current = chart;

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    candlestickSeriesRef.current = candlestickSeries;

    // Create EMA series
    const ema21Series = chart.addLineSeries({
      color: '#ff9800',
      lineWidth: 2,
    });
    ema21SeriesRef.current = ema21Series;

    const ema50Series = chart.addLineSeries({
      color: '#2196f3',
      lineWidth: 2,
    });
    ema50SeriesRef.current = ema50Series;

    // Signal markers will be added directly to the main series using setMarkers
    // No need for separate line series

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  };

  const updateChart = () => {
    if (!chartRef.current || !candlestickSeriesRef.current || !ema21SeriesRef.current || !ema50SeriesRef.current) {
      console.log('Chart refs not ready:', {
        chart: !!chartRef.current,
        candlestick: !!candlestickSeriesRef.current,
        ema21: !!ema21SeriesRef.current,
        ema50: !!ema50SeriesRef.current
      });
      return;
    }

    const filteredStockData = filterDataByTimeframe(stockData, timeframe);
    
    console.log('Updating chart with data:', {
      stockDataCount: filteredStockData.length,
      timeframe
    });

    // Prepare candlestick data
    const candlestickData: CandlestickData[] = filteredStockData
      .map((data) => ({
        time: (new Date(data.date).getTime() / 1000) as Time,
        open: parseFloat(data.open),
        high: parseFloat(data.high),
        low: parseFloat(data.low),
        close: parseFloat(data.close),
      }))
      .sort((a, b) => (a.time as number) - (b.time as number));

    // Prepare EMA data
    const ema21Data: LineData[] = filteredStockData
      .filter(data => data.ema_21 !== null && data.ema_21 !== undefined)
      .map((data) => ({
        time: (new Date(data.date).getTime() / 1000) as Time,
        value: parseFloat(data.ema_21),
      }))
      .sort((a, b) => (a.time as number) - (b.time as number));

    const ema50Data: LineData[] = filteredStockData
      .filter(data => data.ema_50 !== null && data.ema_50 !== undefined)
      .map((data) => ({
        time: (new Date(data.date).getTime() / 1000) as Time,
        value: parseFloat(data.ema_50),
      }))
      .sort((a, b) => (a.time as number) - (b.time as number));

    // Prepare signal markers
    const signalMarkers: any[] = [];

    if (emaResults && emaResults.signals) {
      const filteredSignals = filterDataByTimeframe(emaResults.signals, timeframe);
      
      filteredSignals.forEach(signal => {
        const marker = {
          time: (new Date(signal.date).getTime() / 1000) as Time,
          position: signal.signal_type === 'BUY' ? 'belowBar' as const : 'aboveBar' as const,
          color: signal.signal_type === 'BUY' ? '#00ff00' : '#ff0000',
          shape: signal.signal_type === 'BUY' ? 'arrowUp' as const : 'arrowDown' as const,
          text: signal.signal_type,
        };
        signalMarkers.push(marker);
      });
    }

    // Update series
    candlestickSeriesRef.current.setData(candlestickData);
    ema21SeriesRef.current.setData(ema21Data);
    ema50SeriesRef.current.setData(ema50Data);
    
    // Update signal markers on the main candlestick series
    candlestickSeriesRef.current.setMarkers(signalMarkers);

    // Reset and fit content to show the full timeframe
    chartRef.current.timeScale().fitContent();
  };

  useEffect(() => {
    const cleanup = initializeChart();
    return cleanup;
  }, []);

  useEffect(() => {
    if (stockData.length > 0 && emaResults) {
      updateChart();
    }
  }, [stockData, emaResults, timeframe]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'success';
    if (value < 0) return 'error';
    return 'default';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        EMA Trading Chart
      </Typography>
      
      <Typography variant="subtitle1" color="textSecondary" sx={{ mb: 3 }}>
        Price chart with 21 EMA, 50 EMA, and trading signals
      </Typography>

      {/* Input Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <Autocomplete
                freeSolo
                options={availableSymbols}
                value={symbol}
                onInputChange={(event, newValue) => {
                  setSymbol(newValue?.toUpperCase() || '');
                }}
                onChange={(event, newValue) => {
                  if (newValue && typeof newValue === 'string') {
                    setSymbol(newValue.toUpperCase());
                  }
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Stock Symbol"
                    placeholder="e.g., AAPL"
                    InputProps={{
                      ...params.InputProps,
                    }}
                  />
                )}
                filterOptions={(options, { inputValue }) => {
                  const filtered = options.filter(option =>
                    option.toLowerCase().startsWith(inputValue.toLowerCase())
                  );
                  return filtered.slice(0, 10); // Limit to 10 suggestions
                }}
              />
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
            <TextField
              fullWidth
              label="Days to Analyze (0 = All Data)"
              type="number"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              inputProps={{ min: 0, max: 2000 }}
              helperText="Use 0 for all available data"
            />
            <TextField
              fullWidth
              label="ATR Period"
              type="number"
              value={atrPeriod}
              onChange={(e) => setAtrPeriod(Number(e.target.value))}
              inputProps={{ min: 5, max: 50 }}
              helperText="Period for Average True Range calculation"
            />
            <TextField
              fullWidth
              label="ATR Multiplier"
              type="number"
              value={atrMultiplier}
              onChange={(e) => setAtrMultiplier(Number(e.target.value))}
              inputProps={{ min: 0.5, max: 5.0, step: 0.1 }}
              helperText="Multiplier for trailing stop distance (e.g., 2.0 = 2x ATR)"
            />
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <FormControl fullWidth>
                <InputLabel>Timeframe</InputLabel>
                <Select
                  value={timeframe}
                  label="Timeframe"
                  onChange={(e) => setTimeframe(e.target.value)}
                >
                  <MenuItem value="all">All Time</MenuItem>
                  <MenuItem value="1m">1 Month</MenuItem>
                  <MenuItem value="3m">3 Months</MenuItem>
                  <MenuItem value="6m">6 Months</MenuItem>
                  <MenuItem value="1y">1 Year</MenuItem>
                  <MenuItem value="2y">2 Years</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <Button
                variant="contained"
                onClick={loadData}
                disabled={loading}
                fullWidth
                sx={{ height: '56px' }}
              >
                {loading ? <CircularProgress size={24} /> : 'Load Chart'}
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

      {/* Chart */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {symbol} - EMA Trading Chart
          </Typography>
          

          <Box
            ref={chartContainerRef}
            sx={{
              width: '100%',
              height: '500px',
              border: '1px solid #2B2B43',
              borderRadius: '4px',
            }}
          />
        </CardContent>
      </Card>

      {/* Performance Summary */}
      {emaResults && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              EMA Trading Performance - {emaResults.symbol}
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Period: {new Date(emaResults.start_date).toLocaleDateString()} to {new Date(emaResults.end_date).toLocaleDateString()} 
              ({emaResults.total_days} days)
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                <Typography variant="h4" color={getPerformanceColor(emaResults.performance_metrics.total_return_percent)}>
                  {formatPercent(emaResults.performance_metrics.total_return_percent)}
                </Typography>
                <Typography variant="caption">Total Return</Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                <Typography variant="h4" color={getPerformanceColor(emaResults.performance_metrics.total_pnl)}>
                  {formatCurrency(emaResults.performance_metrics.total_pnl)}
                </Typography>
                <Typography variant="caption">Total P&L</Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                <Typography variant="h4">
                  {emaResults.performance_metrics.total_trades}
                </Typography>
                <Typography variant="caption">Total Trades</Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                <Typography variant="h4" color={getPerformanceColor(emaResults.performance_metrics.win_rate - 50)}>
                  {formatPercent(emaResults.performance_metrics.win_rate)}
                </Typography>
                <Typography variant="caption">Win Rate</Typography>
              </Box>
            </Box>

            {/* Trading Trades Table */}
            {emaResults.trades && emaResults.trades.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Trading Trades ({timeframe === 'all' ? 'All Time' : timeframe.toUpperCase()})
                </Typography>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Entry Date</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Exit Date</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Entry Price</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Exit Price</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Shares</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>P&L</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>P&L %</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Duration</th>
                      <th style={{ padding: '8px', textAlign: 'center' }}>Exit Reason</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Running Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const filteredTrades = filterDataByTimeframe(emaResults.trades, timeframe);
                      let runningTotal = 0;
                      return filteredTrades.map((trade, index) => {
                        runningTotal += trade.pnl || 0;
                        return (
                          <tr key={index}>
                            <td style={{ padding: '8px' }}>
                              {new Date(trade.entry_date).toLocaleDateString()}
                            </td>
                            <td style={{ padding: '8px' }}>
                              {trade.exit_date ? new Date(trade.exit_date).toLocaleDateString() : 'Open'}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              ${trade.entry_price.toFixed(2)}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              {trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : 'Open'}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              {trade.shares.toLocaleString()}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              {trade.pnl ? (
                                <span style={{ color: trade.pnl >= 0 ? 'green' : 'red' }}>
                                  ${trade.pnl.toFixed(2)}
                                </span>
                              ) : 'Open'}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              {trade.pnl_percent ? (
                                <span style={{ color: trade.pnl_percent >= 0 ? 'green' : 'red' }}>
                                  {trade.pnl_percent.toFixed(2)}%
                                </span>
                              ) : 'Open'}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              {trade.duration_days ? `${trade.duration_days} days` : 'Open'}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'center' }}>
                              {trade.exit_reason ? (
                                <span style={{ 
                                  color: trade.exit_reason === 'TRAILING_STOP' ? 'orange' : 'blue',
                                  fontWeight: 'bold'
                                }}>
                                  {trade.exit_reason === 'TRAILING_STOP' ? 'Trailing Stop' : 'EMA Signal'}
                                </span>
                              ) : 'Open'}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right', fontWeight: 'bold' }}>
                              <span style={{ color: runningTotal >= 0 ? 'green' : 'red' }}>
                                ${runningTotal.toFixed(2)}
                              </span>
                            </td>
                          </tr>
                        );
                      });
                    })()}
                  </tbody>
                </table>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default EMAChart;
