# AI-AV-Agent Network Monitoring Dashboard

A modern, Domotz-inspired network monitoring dashboard built with React, Tailwind CSS, and integrated with the AI-AV-Agent platform.

## Features

### 🎨 Modern UI Design
- **Dark Theme**: Professional dark theme with clean aesthetics
- **Responsive Layout**: Adapts seamlessly to different screen sizes
- **Smooth Animations**: Framer Motion powered transitions and animations
- **Card-Based Components**: Modular, reusable UI components with subtle shadows

### 🏢 Dashboard Overview
- **Status Cards**: Real-time metrics for Total Rooms, Active Meetings, Network Health, and Alerts
- **Network Topology**: Interactive D3.js visualization showing connected devices with status indicators
- **Device List**: Sortable table with device details, status, and uptime information
- **Mini Graphs**: Bandwidth usage and latency trends over 24 hours
- **Alert Feed**: Real-time alert notifications in sidebar

### 📊 Room Monitoring
- **Grid/List View**: Toggle between card grid and list view
- **Status Indicators**: Color-coded status (Available, In-Use, Offline)
- **Room Cards**: Display room name, status, occupancy, health, and equipment info
- **Quick Actions**: View details, run diagnostics, or join meetings
- **Search & Filter**: Filter rooms by status and search by name

### 🌐 Network Devices
- **Device Table**: Comprehensive table with sorting and filtering
- **Topology View**: Interactive network map showing device connections
- **Device Details Panel**: Sliding panel with device info, performance metrics, and alerts
- **Real-time Status**: Live updates of device status and connectivity

### 📈 Analytics
- **Utilization Trends**: Weekly and daily utilization charts
- **Status Distribution**: Pie chart showing room status breakdown
- **Peak Hours**: Line chart identifying peak usage times
- **Room Ranking**: Top utilized rooms with meeting counts
- **Heatmap**: Hourly utilization heatmap across all rooms

### 🔔 Alerts & Notifications
- **Alert Dashboard**: Categorized alerts by severity (Critical, Warning, Info)
- **Real-time Updates**: Live alert feed with timestamps
- **Filtering**: Filter by severity and status
- **Dismissal Actions**: Dismiss individual or all alerts
- **Export**: Export alerts for reporting

### ⚙️ Settings
- **General Settings**: Refresh interval, theme, timezone, default view
- **Notifications**: Email, Slack, and alert type preferences
- **Monitoring**: Health check intervals, performance tracking
- **Advanced**: Data retention, log levels, API timeout

## Technology Stack

- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Animation library
- **D3.js**: Network topology visualization
- **Recharts**: Chart and graph library
- **Axios**: HTTP client for API calls
- **React Router**: Client-side routing
- **React Icons**: Icon library
- **React Toastify**: Toast notifications

## Color Scheme

- **Green (#10b981)**: Healthy/Available status
- **Yellow (#f59e0b)**: Warning status
- **Red (#ef4444)**: Critical/Error status
- **Blue (#3b82f6)**: Primary actions and info
- **Dark (#030712 - #1f2937)**: Background and cards

## Installation

### Prerequisites
- Node.js 18+ and npm/yarn
- Running AI-AV-Agent Flask backend on port 5000

### Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Access the dashboard**:
   Open http://localhost:3000 in your browser

### Build for Production

```bash
npm run build
```

The build output will be in `../dashboard/static/dist` for Flask to serve.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Sidebar.jsx        # Collapsible navigation sidebar
│   │   │   └── Header.jsx         # Top header with search and notifications
│   │   └── UI/
│   │       ├── StatusCard.jsx     # Metric display cards
│   │       ├── RoomCard.jsx       # Room status cards
│   │       ├── DeviceTable.jsx    # Device list table
│   │       ├── NetworkTopology.jsx # D3.js network visualization
│   │       ├── DeviceDetailsPanel.jsx # Sliding device details
│   │       └── AlertsList.jsx     # Alert feed component
│   ├── pages/
│   │   ├── Dashboard.jsx          # Main dashboard page
│   │   ├── Rooms.jsx              # Rooms monitoring page
│   │   ├── NetworkDevices.jsx     # Network devices page
│   │   ├── Analytics.jsx          # Analytics and reports
│   │   ├── Alerts.jsx             # Alerts management
│   │   └── Settings.jsx           # Settings and configuration
│   ├── services/
│   │   └── api.js                 # API client and endpoints
│   ├── App.jsx                    # Main app component
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles and Tailwind
├── index.html                     # HTML template
├── vite.config.js                 # Vite configuration
├── tailwind.config.js             # Tailwind CSS configuration
├── postcss.config.js              # PostCSS configuration
└── package.json                   # Dependencies and scripts
```

## API Integration

The dashboard connects to the Flask backend API:

- **Base URL**: `http://localhost:5000/api`
- **Proxy**: Vite dev server proxies `/api` requests to Flask backend
- **Endpoints Used**:
  - `GET /health` - Health check
  - `GET /zoom/rooms` - Get all rooms
  - `GET /zoom/rooms/:id` - Get room details
  - `GET /zoom/dashboard` - Dashboard overview
  - `GET /zoom/health-summary` - Health summary
  - `GET /utilization/summary` - Utilization analytics
  - `GET /utilization/ranking` - Room ranking
  - `GET /utilization/heatmap` - Utilization heatmap

## Development

### Hot Module Replacement
Vite provides instant HMR for fast development.

### Code Organization
- **Components**: Reusable UI components in `components/`
- **Pages**: Full page components in `pages/`
- **Services**: API calls and business logic in `services/`
- **Styles**: Tailwind utilities + custom CSS in `index.css`

### Adding New Features
1. Create component in appropriate folder
2. Add route in `App.jsx` if needed
3. Connect to API via `services/api.js`
4. Use existing UI components for consistency

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Performance

- **Code Splitting**: React lazy loading for routes
- **Optimized Builds**: Vite production builds with tree-shaking
- **Lazy Images**: Images load on demand
- **Memoization**: React.memo for expensive components

## Customization

### Colors
Edit `tailwind.config.js` to customize the color palette.

### Layout
Modify `components/Layout/Sidebar.jsx` and `Header.jsx` for layout changes.

### Branding
Update logo and app name in `Sidebar.jsx`.

## Troubleshooting

### CORS Issues
Ensure Flask backend has CORS enabled (already configured in `zoom_dashboard_app.py`).

### API Connection Failed
1. Verify Flask backend is running on port 5000
2. Check `.env` file has correct Zoom API credentials
3. Review browser console for errors

### Build Errors
1. Delete `node_modules` and reinstall: `npm install`
2. Clear Vite cache: `rm -rf .vite`
3. Check Node.js version: `node --version` (should be 18+)

## License

This project is part of the AI-AV-Agent platform. See LICENSE in the root directory.

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## Support

For issues and questions, please open an issue on the GitHub repository.
