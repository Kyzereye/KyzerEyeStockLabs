import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  ExpandMore,
  ArrowBack,
  Timeline,
  TrendingUp,
  TrendingDown,
  Assessment,
} from '@mui/icons-material';
import { createChart, IChartApi, ISeriesApi, CandlestickData, HistogramData } from 'lightweight-charts';
import apiService, { StockData, WyckoffSignal, Trade } from '../services/api';

interface ChartViewerState {
  loading: boolean;
  loadingBacktest: boolean;
  error: string | null;
  stockData: StockData[];
  wyckoffSignals: WyckoffSignal[];
  trades: Trade[];
  phaseTransitions: Array<{
    phase: string;
    startDate: string;
    endDate: string;
    duration: number;
  }>;
  backtestResult: any;
}

const ChartViewer: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const buySignalSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const sellSignalSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const phaseTransitionLinesRef = useRef<ISeriesApi<"Area">[]>([]);
  
  const [state, setState] = useState<ChartViewerState>({
    loading: true,
    loadingBacktest: false,
    error: null,
    stockData: [],
    wyckoffSignals: [],
    trades: [],
    phaseTransitions: [],
    backtestResult: null,
  });

         const [showVolume, setShowVolume] = useState(false);
  const [timeframe, setTimeframe] = useState('all');
  const [tradeFilter, setTradeFilter] = useState<'all' | 'buy' | 'sell'>('all');

  const timeframeOptions = [
    { value: '1m', label: '1 Month' },
    { value: '3m', label: '3 Months' },
    { value: '6m', label: '6 Months' },
    { value: '1y', label: '1 Year' },
    { value: 'all', label: 'All Data' },
  ];

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
      default:
        return data;
    }
    
    return data.filter(item => {
      const itemDate = new Date(item.date);
      return itemDate >= cutoffDate;
    });
  };

  useEffect(() => {
    if (symbol) {
      loadChartData();
    }
  }, [symbol]);

  useEffect(() => {
    if (state.stockData.length > 0 && chartContainerRef.current) {
      initializeChart();
    }
    
    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
      buySignalSeriesRef.current = null;
      sellSignalSeriesRef.current = null;
      phaseTransitionLinesRef.current = [];
    };
  }, [state.stockData]);

  useEffect(() => {
    if (volumeSeriesRef.current) {
      if (showVolume) {
        volumeSeriesRef.current.applyOptions({ visible: true });
      } else {
        volumeSeriesRef.current.applyOptions({ visible: false });
      }
    }
  }, [showVolume]);

  useEffect(() => {
    if (state.stockData.length > 0 && candlestickSeriesRef.current && volumeSeriesRef.current) {
      updateChartWithTimeframe();
    }
  }, [timeframe, state.stockData]);

  useEffect(() => {
    // Update chart with phase sections when Wyckoff signals are loaded
    if (state.wyckoffSignals.length > 0 && chartRef.current) {
      addWyckoffPhaseSections(chartRef.current, state.wyckoffSignals);
    }
  }, [state.wyckoffSignals]);

  const loadChartData = async () => {
    if (!symbol) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Load stock data first (fast)
      const stockData = await apiService.getStockData(symbol);
      
      setState(prev => ({
        ...prev,
        loading: false,
        stockData,
      }));

      // Load backtest data in background (slow)
      setState(prev => ({ ...prev, loadingBacktest: true }));
      try {
        const backtestResult = await apiService.getSymbolBacktest(symbol);
        setState(prev => ({
          ...prev,
          wyckoffSignals: backtestResult.signals,
          trades: backtestResult.trades,
          backtestResult,
          loadingBacktest: false,
        }));
      } catch (backtestError) {
        console.warn(`Backtest data unavailable for ${symbol}:`, backtestError);
        setState(prev => ({ ...prev, loadingBacktest: false }));
        // Continue without backtest data - chart will still work
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load chart data',
      }));
    }
  };

  const loadBacktestData = async () => {
    if (!symbol) return;
    
    setState(prev => ({ ...prev, loadingBacktest: true }));
    try {
      const backtestResult = await apiService.getSymbolBacktest(symbol);
      setState(prev => ({
        ...prev,
        wyckoffSignals: backtestResult.signals,
        trades: backtestResult.trades,
        backtestResult,
        loadingBacktest: false,
      }));
    } catch (error) {
      console.error(`Failed to load backtest data for ${symbol}:`, error);
      setState(prev => ({ ...prev, loadingBacktest: false }));
    }
  };

  const updateChartWithTimeframe = () => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current) return;

    // Filter data based on timeframe
    const filteredStockData = filterDataByTimeframe(state.stockData, timeframe);
    const filteredSignals = filterDataByTimeframe(state.wyckoffSignals, timeframe);

    console.log(`Updating chart with ${filteredStockData.length} data points for timeframe: ${timeframe}`);

    // Prepare filtered candlestick data
    const candlestickData: CandlestickData[] = filteredStockData
      .map((data) => ({
        time: (new Date(data.date).getTime() / 1000) as any,
        open: parseFloat(data.open.toString()),
        high: parseFloat(data.high.toString()),
        low: parseFloat(data.low.toString()),
        close: parseFloat(data.close.toString()),
      }))
      .sort((a, b) => a.time - b.time);

    // Prepare filtered volume data
    const volumeData = filteredStockData
      .map((data) => ({
        time: (new Date(data.date).getTime() / 1000) as any,
        value: parseFloat(data.volume.toString()),
        color: parseFloat(data.close.toString()) >= parseFloat(data.open.toString()) ? '#26a69a' : '#ef5350',
      }))
      .sort((a, b) => a.time - b.time);

    // Update chart data
    candlestickSeriesRef.current.setData(candlestickData);
    volumeSeriesRef.current.setData(volumeData);


           // Update Wyckoff phase sections with filtered data
           if (chartRef.current) {
             addWyckoffPhaseSections(chartRef.current, filteredSignals);
           }
  };

  const initializeChart = () => {
    if (!chartContainerRef.current || chartRef.current) return;
    
    console.log('Initializing chart with', state.stockData.length, 'data points');
    if (state.stockData.length === 0) {
      console.warn('No stock data available for chart');
      return;
    }

           console.log('Initializing chart with', state.wyckoffSignals.length, 'signals');

           // Create chart
           const chart = createChart(chartContainerRef.current, {
             width: chartContainerRef.current.clientWidth,
             height: 500,
             layout: {
               background: { color: '#1a1a1a' }, // Default dark background
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
        borderColor: '#485c7b',
      },
      timeScale: {
        borderColor: '#485c7b',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Add candlestick series using v4 API (with type assertion)
    const candlestickSeries = (chart as any).addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    candlestickSeriesRef.current = candlestickSeries;

    // Add volume series using v4 API (with type assertion) - hidden by default
    const volumeSeries = (chart as any).addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
      visible: showVolume, // Set initial visibility based on showVolume state
    });
    volumeSeriesRef.current = volumeSeries;

    // Configure volume scale
    (chart as any).priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.7,
        bottom: 0,
      },
    });

    // Prepare and sort candlestick data by time (ascending order)
    const candlestickData: CandlestickData[] = state.stockData
      .map((data) => ({
        time: (new Date(data.date).getTime() / 1000) as any,
        open: parseFloat(data.open.toString()),
        high: parseFloat(data.high.toString()),
        low: parseFloat(data.low.toString()),
        close: parseFloat(data.close.toString()),
      }))
      .sort((a, b) => a.time - b.time);

    // Prepare and sort volume data by time (ascending order)
    const volumeData = state.stockData
      .map((data) => ({
        time: (new Date(data.date).getTime() / 1000) as any,
        value: parseFloat(data.volume.toString()),
        color: parseFloat(data.close.toString()) >= parseFloat(data.open.toString()) ? '#26a69a' : '#ef5350',
      }))
      .sort((a, b) => a.time - b.time);

    // Debug: Log first few data points to verify sorting and data types
    console.log('First 3 candlestick data points:', candlestickData.slice(0, 3));
    console.log('Last 3 candlestick data points:', candlestickData.slice(-3));
    console.log('Data types - open:', typeof candlestickData[0]?.open, 'volume:', typeof volumeData[0]?.value);

           // Set data
           candlestickSeries.setData(candlestickData);
           volumeSeries.setData(volumeData);


           // Add Wyckoff phase sections if signals are available
           if (state.wyckoffSignals && state.wyckoffSignals.length > 0) {
             addWyckoffPhaseSections(chart, state.wyckoffSignals);
           }

    // Fit content
    chart.timeScale().fitContent();

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
    };
  };



         const addWyckoffPhaseSections = (chart: IChartApi, signals: WyckoffSignal[]) => {
           if (!signals || signals.length === 0) return;

           console.log('Processing Wyckoff phase information for', signals.length, 'signals');

           // Remove existing signal series if they exist
           if (buySignalSeriesRef.current) {
             chart.removeSeries(buySignalSeriesRef.current);
             buySignalSeriesRef.current = null;
           }
           if (sellSignalSeriesRef.current) {
             chart.removeSeries(sellSignalSeriesRef.current);
             sellSignalSeriesRef.current = null;
           }

           // Remove existing phase transition lines
           phaseTransitionLinesRef.current.forEach(lineSeries => {
             chart.removeSeries(lineSeries);
           });
           phaseTransitionLinesRef.current = [];

           // Process phase information and store it for display
           const phaseTransitions: Array<{
             phase: string;
             startDate: string;
             endDate: string;
             duration: number;
           }> = [];

           let currentPhase = signals[0]?.phase;
           let phaseStartTime = signals[0]?.date;
           
           for (let i = 1; i < signals.length; i++) {
             const signal = signals[i];
             
             if (signal.phase !== currentPhase) {
               // Phase change - record the previous phase
               const startDate = new Date(phaseStartTime);
               const endDate = new Date(signal.date);
               const duration = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)); // days
               
               phaseTransitions.push({
                 phase: currentPhase,
                 startDate: phaseStartTime,
                 endDate: signal.date,
                 duration: duration
               });
               
               console.log(`Phase: ${currentPhase} from ${phaseStartTime} to ${signal.date} (${duration} days)`);
               
               // Start new phase
               currentPhase = signal.phase;
               phaseStartTime = signal.date;
             }
           }

           // Handle the last phase
           if (currentPhase && phaseStartTime) {
             const lastSignal = signals[signals.length - 1];
             const startDate = new Date(phaseStartTime);
             const endDate = new Date(lastSignal.date);
             const duration = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)); // days
             
             phaseTransitions.push({
               phase: currentPhase,
               startDate: phaseStartTime,
               endDate: lastSignal.date,
               duration: duration
             });
             
             console.log(`Final Phase: ${currentPhase} from ${phaseStartTime} to ${lastSignal.date} (${duration} days)`);
           }

           // Add colored background areas for Wyckoff phases
           phaseTransitions.forEach((transition, index) => {
             const startTime = (new Date(transition.startDate).getTime() / 1000) as any;
             const endTime = index < phaseTransitions.length - 1 
               ? (new Date(phaseTransitions[index + 1].startDate).getTime() / 1000) as any
               : (new Date().getTime() / 1000) as any;
             
             const phaseColor = getPhaseColor(transition.phase);
             
             // Add area series for background coloring
             const areaSeries = chart.addAreaSeries({
               lineColor: phaseColor,
               topColor: phaseColor + '40', // 25% opacity
               bottomColor: phaseColor + '40', // 25% opacity
               priceScaleId: 'left',
             });
             
             // Store the series reference for cleanup
             phaseTransitionLinesRef.current.push(areaSeries);
             
             // Get price range for the background area
             const candlestickData = candlestickSeriesRef.current?.data();
             if (candlestickData && candlestickData.length > 0) {
               const validCandlestickData = candlestickData.filter(d => 'high' in d && 'low' in d);
               if (validCandlestickData.length > 0) {
                 const prices = validCandlestickData.map(d => [(d as any).high, (d as any).low]).flat();
                 const minPrice = Math.min(...prices);
                 const maxPrice = Math.max(...prices);
                 const priceRange = maxPrice - minPrice;
                 const areaTop = maxPrice + priceRange * 0.5; // 50% bigger
                 const areaBottom = minPrice - priceRange * 0.5; // 50% bigger
                 
                 // Add area data points for the phase period
                 const areaData = [];
                 for (let time = startTime; time <= endTime; time += 86400) { // Daily intervals
                   areaData.push({
                     time: time,
                     value: areaTop
                   });
                 }
                 
                 areaSeries.setData(areaData);
                 
                 console.log(`Added phase background area for ${transition.phase} from ${transition.startDate}`);
               }
             }
           });

           // Store phase transitions for display
           setState(prev => ({ ...prev, phaseTransitions }));
         };

  const getPhaseColor = (phase: string) => {
    // Authentic Wyckoff Method phase colors
    if (phase.includes('Phase A') || phase.includes('Selling Climax')) return '#4caf50'; // Green for accumulation start
    if (phase.includes('Phase B') || phase.includes('Building Cause')) return '#8bc34a'; // Light green for building cause
    if (phase.includes('Phase C') || phase.includes('Spring')) return '#cddc39'; // Yellow-green for spring test
    if (phase.includes('Phase D') || phase.includes('Markup')) return '#2196f3'; // Blue for markup
    if (phase.includes('Phase E') || phase.includes('Climax')) return '#ff9800'; // Orange for climax
    if (phase.includes('Distribution')) return '#f44336'; // Red for distribution
    if (phase.includes('Markdown')) return '#ff5722'; // Deep orange for markdown
    if (phase.includes('Accumulation')) return '#4caf50'; // Green for accumulation
    return '#9e9e9e'; // Default gray
  };

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'success';
    if (value < 0) return 'error';
    return 'default';
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

  // Trade filtering and statistics
  const getFilteredTrades = () => {
    if (tradeFilter === 'all') return state.trades;
    return state.trades.filter(trade => trade.action.toLowerCase() === tradeFilter);
  };

  const getTradeStatistics = () => {
    const filteredTrades = getFilteredTrades();
    const completedTrades = filteredTrades.filter(trade => trade.exit_date && trade.pnl !== undefined);
    
    if (completedTrades.length === 0) {
      return {
        totalTrades: filteredTrades.length,
        completedTrades: 0,
        totalPnL: 0,
        totalPnLPercent: 0,
        avgPnL: 0,
        avgPnLPercent: 0,
        winRate: 0,
        winningTrades: 0,
        losingTrades: 0,
        largestWin: 0,
        largestLoss: 0
      };
    }

    const totalPnL = completedTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0);
    const totalPnLPercent = completedTrades.reduce((sum, trade) => sum + (trade.pnl_percent || 0), 0);
    const winningTrades = completedTrades.filter(trade => (trade.pnl || 0) > 0);
    const losingTrades = completedTrades.filter(trade => (trade.pnl || 0) < 0);
    const winRate = (winningTrades.length / completedTrades.length) * 100;
    const largestWin = Math.max(...completedTrades.map(trade => trade.pnl || 0));
    const largestLoss = Math.min(...completedTrades.map(trade => trade.pnl || 0));

    return {
      totalTrades: filteredTrades.length,
      completedTrades: completedTrades.length,
      totalPnL,
      totalPnLPercent,
      avgPnL: totalPnL / completedTrades.length,
      avgPnLPercent: totalPnLPercent / completedTrades.length,
      winRate,
      winningTrades: winningTrades.length,
      losingTrades: losingTrades.length,
      largestWin,
      largestLoss
    };
  };

  if (state.loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading chart data for {symbol}...
        </Typography>
      </Box>
    );
  }

  if (state.error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {state.error}
        <Button onClick={loadChartData} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/')}
            sx={{ mr: 2 }}
          >
            Back to Dashboard
          </Button>
          <Typography variant="h4" component="h1">
            {symbol} - Wyckoff Analysis
          </Typography>
        </Box>
      </Box>

      <Box display="flex" flexDirection={{ xs: 'column', lg: 'row' }} gap={3}>
        {/* Chart Placeholder */}
        <Box flex={2}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Price Chart with Authentic Wyckoff Method Analysis
                </Typography>
                <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                  Based on official Wyckoff Method - A-E phases with Point-and-Figure price targets
                </Typography>
                <Box display="flex" alignItems="center" gap={2}>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>Timeframe</InputLabel>
                    <Select
                      value={timeframe}
                      label="Timeframe"
                      onChange={(e) => setTimeframe(e.target.value)}
                    >
                      {timeframeOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body2" color="textSecondary">
                      Volume:
                    </Typography>
                    <Button
                      variant={showVolume ? "contained" : "outlined"}
                      size="small"
                      onClick={() => setShowVolume(!showVolume)}
                      sx={{ minWidth: 'auto', px: 1 }}
                    >
                      {showVolume ? "ON" : "OFF"}
                    </Button>
                  </Box>
                </Box>
              </Box>
                     <Box
                       ref={chartContainerRef}
                       sx={{
                         width: '100%',
                         height: '500px',
                         border: '1px solid',
                         borderColor: 'divider',
                         borderRadius: 1,
                         overflow: 'hidden',
                       }}
                     />
                     <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                       Data points: {filterDataByTimeframe(state.stockData, timeframe).length} | 
                       Signals: {filterDataByTimeframe(state.wyckoffSignals, timeframe).length} | 
                       Trades: {state.trades.length} | 
                       Timeframe: {timeframeOptions.find(opt => opt.value === timeframe)?.label}
                     </Typography>
              
                     {/* Chart Legend */}
                     <Box sx={{ mt: 2, p: 2, backgroundColor: 'background.default', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                       <Typography variant="h6" gutterBottom color="primary">
                         📊 Chart Legend
                       </Typography>
                       
                       {/* Wyckoff Phase Information */}
                       <Box sx={{ mb: 3, p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
                         <Typography variant="subtitle1" gutterBottom color="primary">
                           📊 Wyckoff Phase Types
                         </Typography>
                         <Box display="flex" flexWrap="wrap" gap={2}>
                           <Box display="flex" alignItems="center">
                             <Box sx={{ width: 20, height: 12, backgroundColor: '#4caf50', mr: 1, borderRadius: '2px' }} />
                             <Typography variant="body2" fontWeight="bold">Accumulation</Typography>
                           </Box>
                           <Box display="flex" alignItems="center">
                             <Box sx={{ width: 20, height: 12, backgroundColor: '#f44336', mr: 1, borderRadius: '2px' }} />
                             <Typography variant="body2" fontWeight="bold">Distribution</Typography>
                           </Box>
                           <Box display="flex" alignItems="center">
                             <Box sx={{ width: 20, height: 12, backgroundColor: '#2196f3', mr: 1, borderRadius: '2px' }} />
                             <Typography variant="body2" fontWeight="bold">Markup</Typography>
                           </Box>
                           <Box display="flex" alignItems="center">
                             <Box sx={{ width: 20, height: 12, backgroundColor: '#ff9800', mr: 1, borderRadius: '2px' }} />
                             <Typography variant="body2" fontWeight="bold">Markdown</Typography>
                           </Box>
                           <Box display="flex" alignItems="center">
                             <Box sx={{ width: 20, height: 12, backgroundColor: '#9e9e9e', mr: 1, borderRadius: '2px' }} />
                           </Box>
                         </Box>
                         <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                           Colored background areas show Wyckoff phases on chart - see timeline below for details
                         </Typography>
                       </Box>
                       


                       {/* Volume */}
                       <Box>
                         <Typography variant="subtitle2" gutterBottom>
                           Volume Bars:
                         </Typography>
                         <Box display="flex" alignItems="center">
                           <Box sx={{ 
                             width: 16, 
                             height: 16, 
                             backgroundColor: showVolume ? '#666' : 'transparent', 
                             border: '1px solid #666',
                             mr: 1, 
                             borderRadius: '2px' 
                           }} />
                           <Typography variant="caption">Volume Bars</Typography>
                           <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
                             ({showVolume ? 'Visible' : 'Hidden'})
                           </Typography>
                         </Box>
                       </Box>
                     </Box>
            </CardContent>
          </Card>

          {/* Wyckoff Phase Timeline */}
          {state.phaseTransitions.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom color="primary">
                  📊 Wyckoff Phase Timeline
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Chronological breakdown of Wyckoff phases with dates and duration
                </Typography>
                <Box sx={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {state.phaseTransitions.map((transition, index) => (
                    <Box
                      key={index}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        p: 1.5,
                        mb: 1,
                        backgroundColor: 'action.hover',
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Box
                        sx={{
                          width: 20,
                          height: 20,
                          backgroundColor: getPhaseColor(transition.phase),
                          borderRadius: '50%',
                          mr: 2,
                          flexShrink: 0,
                        }}
                      />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {transition.phase}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {new Date(transition.startDate).toLocaleDateString()} - {new Date(transition.endDate).toLocaleDateString()}
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="body2" fontWeight="bold">
                          {transition.duration} days
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          )}
        </Box>

        {/* Analysis Panel */}
        <Box flex={1}>
          {/* Performance Summary */}
          {state.loadingBacktest && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  <CircularProgress size={24} />
                  <Typography variant="body2" color="textSecondary">
                    Loading Wyckoff analysis...
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}
          
          {!state.backtestResult && !state.loadingBacktest && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Wyckoff Analysis
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Run Wyckoff analysis to see trading signals, phases, and performance metrics.
                </Typography>
                <Button
                  variant="contained"
                  onClick={loadBacktestData}
                  disabled={state.loadingBacktest}
                  startIcon={<Assessment />}
                >
                  Run Wyckoff Analysis
                </Button>
              </CardContent>
            </Card>
          )}
          
          {state.backtestResult && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Summary
                </Typography>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Total Return
                    </Typography>
                    <Typography
                      variant="h6"
                      color={getPerformanceColor(state.backtestResult.performance_metrics.total_return_percent)}
                    >
                      {state.backtestResult.performance_metrics.total_return_percent.toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Final Value
                    </Typography>
                    <Typography variant="h6">
                      {formatCurrency(state.backtestResult.performance_metrics.final_value)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Win Rate
                    </Typography>
                    <Typography variant="h6">
                      {state.backtestResult.performance_metrics.win_rate.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Total Trades
                    </Typography>
                    <Typography variant="h6">
                      {state.backtestResult.performance_metrics.total_trades}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Sharpe Ratio
                    </Typography>
                    <Typography variant="h6">
                      {state.backtestResult.performance_metrics.sharpe_ratio.toFixed(2)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Max Drawdown
                    </Typography>
                    <Typography variant="h6" color="error">
                      {state.backtestResult.performance_metrics.max_drawdown_percent.toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Wyckoff Phase Analysis */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Wyckoff Phase Analysis
              </Typography>
              {Object.entries(state.backtestResult?.phase_analysis.phase_counts || {}).map(([phase, count]) => (
                <Box key={phase} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Box display="flex" alignItems="center">
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        backgroundColor: getPhaseColor(phase),
                        mr: 1,
                      }}
                    />
                    <Typography variant="body2">{phase}</Typography>
                  </Box>
                  <Chip label={count as number} size="small" />
                </Box>
              ))}
            </CardContent>
          </Card>

          {/* Recent Signals */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Wyckoff Signals
              </Typography>
              <List dense>
                {state.wyckoffSignals.slice(-10).reverse().map((signal, index) => (
                  <React.Fragment key={index}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemText
                        primary={
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="body2">
                              {formatDate(signal.date)}
                            </Typography>
                            <Chip
                              label={signal.action}
                              color={signal.action === 'BUY' ? 'success' : signal.action === 'SELL' ? 'error' : 'default'}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="caption" color="textSecondary">
                              Phase: {signal.phase} | Price: {formatCurrency(signal.price)}
                            </Typography>
                            <Typography variant="caption" display="block" color="textSecondary">
                              {signal.reasoning}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < state.wyckoffSignals.slice(-10).length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Trade History */}
      <Box mt={3}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h6">
                Trade History
              </Typography>
              <Box display="flex" gap={1}>
                <Button
                  variant={tradeFilter === 'all' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setTradeFilter('all')}
                >
                  All ({state.trades.length})
                </Button>
                <Button
                  variant={tradeFilter === 'buy' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setTradeFilter('buy')}
                  color="success"
                >
                  Buys ({state.trades.filter(t => t.action === 'BUY').length})
                </Button>
                <Button
                  variant={tradeFilter === 'sell' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setTradeFilter('sell')}
                  color="error"
                >
                  Sells ({state.trades.filter(t => t.action === 'SELL').length})
                </Button>
              </Box>
            </Box>

            {/* Trade Statistics */}
            {state.trades.length > 0 && (
              <Box mb={3}>
                <Typography variant="subtitle1" gutterBottom>
                  {tradeFilter === 'all' ? 'All Trades' : 
                   tradeFilter === 'buy' ? 'Buy Trades' : 'Sell Trades'} Statistics
                </Typography>
                <Box display="grid" gridTemplateColumns={{ xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }} gap={2}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Total P&L
                    </Typography>
                    <Typography 
                      variant="h6" 
                      color={getTradeStatistics().totalPnL >= 0 ? 'success.main' : 'error.main'}
                    >
                      {formatCurrency(getTradeStatistics().totalPnL)}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {getTradeStatistics().totalPnLPercent.toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Win Rate
                    </Typography>
                    <Typography variant="h6">
                      {getTradeStatistics().winRate.toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {getTradeStatistics().winningTrades}W / {getTradeStatistics().losingTrades}L
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Avg P&L
                    </Typography>
                    <Typography 
                      variant="h6"
                      color={getTradeStatistics().avgPnL >= 0 ? 'success.main' : 'error.main'}
                    >
                      {formatCurrency(getTradeStatistics().avgPnL)}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {getTradeStatistics().avgPnLPercent.toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Best / Worst
                    </Typography>
                    <Typography variant="body2" color="success.main">
                      {formatCurrency(getTradeStatistics().largestWin)}
                    </Typography>
                    <Typography variant="body2" color="error.main">
                      {formatCurrency(getTradeStatistics().largestLoss)}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            )}
            {getFilteredTrades().length === 0 ? (
              <Box textAlign="center" py={4}>
                <Typography variant="h6" color="textSecondary">
                  No {tradeFilter === 'all' ? '' : tradeFilter} trades found
                </Typography>
              </Box>
            ) : (
              <List>
                {getFilteredTrades().map((trade, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
                      <Typography variant="subtitle1">
                        {formatDate(trade.entry_date)} - {trade.exit_date ? formatDate(trade.exit_date) : 'Open'}
                      </Typography>
                      <Box display="flex" gap={1}>
                        <Chip
                          label={trade.action}
                          color={trade.action === 'BUY' ? 'success' : trade.action === 'SELL' ? 'error' : 'default'}
                          size="small"
                        />
                        {trade.pnl_percent && (
                          <Chip
                            label={`${trade.pnl_percent > 0 ? '+' : ''}${trade.pnl_percent.toFixed(2)}%`}
                            color={trade.pnl_percent > 0 ? 'success' : 'error'}
                            size="small"
                          />
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
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default ChartViewer;