# KyzerEye Stock Labs - React Frontend

A professional trading interface for Wyckoff Method analysis and backtesting.

## 🚀 Features

- **Interactive Dashboard**: Overview of all backtest results and performance metrics
- **TradingView Charts**: Professional candlestick charts with Wyckoff signal overlays
- **Backtest Viewer**: Detailed analysis of trading performance and trade history
- **Real-time Data**: Live connection to Flask backend API
- **Responsive Design**: Works on desktop and mobile devices

## 🛠️ Technology Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for professional UI components
- **TradingView Lightweight Charts** for advanced charting
- **Axios** for API communication
- **React Router** for navigation

## 📦 Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The application will be available at `http://localhost:3000`

## 🌐 API Integration

The frontend connects to the Flask backend API running on `http://localhost:5001`:

### Key Endpoints:
- `GET /api/backtest/results` - Get latest backtest results
- `POST /api/backtest/run` - Run new backtest
- `GET /api/backtest/<symbol>` - Get symbol-specific backtest
- `GET /api/wyckoff/report` - Get Wyckoff analysis report

## 📊 Components

### Dashboard (`/`)
- Performance overview cards
- Top performers table
- Current Wyckoff analysis summary
- Quick access to charts and reports

### Backtest Viewer (`/backtest`)
- Historical backtest report selection
- Detailed performance metrics
- Trade history analysis
- Symbol comparison tools

### Chart Viewer (`/chart/:symbol`)
- Interactive TradingView charts
- Wyckoff phase visualization
- Trade signal overlays
- Performance metrics panel

## 🎨 UI Features

- **Dark Theme**: Professional trading interface design
- **Responsive Layout**: Adapts to different screen sizes
- **Loading States**: Smooth user experience during data loading
- **Error Handling**: User-friendly error messages and retry options
- **Interactive Elements**: Hover effects, tooltips, and expandable sections

## 🔧 Development

### Project Structure:
```
src/
├── components/          # React components
│   ├── Dashboard.tsx    # Main dashboard
│   ├── BacktestViewer.tsx # Backtest analysis
│   └── ChartViewer.tsx  # Trading charts
├── services/           # API services
│   └── api.ts         # Backend communication
├── App.tsx            # Main app component
└── App.css           # Global styles
```

### Key Features:
- **TypeScript**: Full type safety for API responses and components
- **Material-UI**: Consistent design system with dark theme
- **TradingView Integration**: Professional charting capabilities
- **State Management**: React hooks for component state
- **Error Boundaries**: Graceful error handling

## 🚀 Getting Started

1. **Start Backend**: Ensure Flask API is running on port 5001
2. **Start Frontend**: Run `npm start` in the frontend directory
3. **Open Browser**: Navigate to `http://localhost:3000`
4. **Run Backtest**: Click "Run New Backtest" to generate fresh data
5. **View Charts**: Click on any symbol to see detailed Wyckoff analysis

## 📱 Mobile Support

The interface is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

## 🎯 Next Steps

- Add more chart indicators
- Implement real-time data updates
- Add portfolio management features
- Create export functionality for reports
- Add user authentication and preferences

## 🔗 Backend Integration

This frontend is designed to work with the KyzerEye Stock Labs Flask backend:
- Stock data collection and storage
- Wyckoff analysis algorithms
- Backtesting engine
- Performance metrics calculation

For backend setup, see the main project README.