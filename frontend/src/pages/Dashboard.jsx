import React, { useState, useEffect } from 'react'
import { FiMonitor, FiActivity, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi'
import { HiOutlineServerStack } from 'react-icons/hi2'
import StatusCard from '../components/UI/StatusCard'
import RoomCard from '../components/UI/RoomCard'
import DeviceTable from '../components/UI/DeviceTable'
import NetworkTopology from '../components/UI/NetworkTopology'
import AlertsList from '../components/UI/AlertsList'
import DeviceDetailsPanel from '../components/UI/DeviceDetailsPanel'
import { getDashboard, getHealthSummary, getRooms } from '../services/api'
import { toast } from 'react-toastify'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const Dashboard = () => {
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [healthSummary, setHealthSummary] = useState(null)
  const [rooms, setRooms] = useState([])
  const [selectedDevice, setSelectedDevice] = useState(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)

  // Mock data for bandwidth and latency trends
  const bandwidthData = [
    { time: '00:00', value: 45 },
    { time: '04:00', value: 38 },
    { time: '08:00', value: 72 },
    { time: '12:00', value: 85 },
    { time: '16:00', value: 78 },
    { time: '20:00', value: 62 },
    { time: '23:59', value: 48 },
  ]

  const latencyData = [
    { time: '00:00', value: 12 },
    { time: '04:00', value: 15 },
    { time: '08:00', value: 28 },
    { time: '12:00', value: 35 },
    { time: '16:00', value: 32 },
    { time: '20:00', value: 18 },
    { time: '23:59', value: 14 },
  ]

  // Mock alerts
  const mockAlerts = [
    {
      id: 1,
      title: 'Device Offline',
      message: 'Zoom Room Controller in Conference Room A is not responding',
      severity: 'critical',
      source: 'Network Monitor',
      timestamp: new Date(Date.now() - 300000),
      room_name: 'Conference Room A',
    },
    {
      id: 2,
      title: 'High Latency',
      message: 'Network latency exceeds threshold (45ms)',
      severity: 'warning',
      source: 'QoS Monitor',
      timestamp: new Date(Date.now() - 900000),
    },
    {
      id: 3,
      title: 'Firmware Update Available',
      message: 'New firmware version available for 3 devices',
      severity: 'info',
      source: 'System',
      timestamp: new Date(Date.now() - 3600000),
    },
  ]

  useEffect(() => {
    fetchDashboardData()
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const [dashboardRes, healthRes, roomsRes] = await Promise.all([
        getDashboard(),
        getHealthSummary(),
        getRooms(true),
      ])

      setDashboardData(dashboardRes.data.data)
      setHealthSummary(healthRes.data.data)
      setRooms(roomsRes.data.data.slice(0, 6)) // Show only first 6 rooms
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const handleDeviceClick = (device) => {
    setSelectedDevice(device)
    setIsPanelOpen(true)
  }

  const handleRoomClick = (room) => {
    toast.info(`Room details: ${room.name}`)
  }

  // Extract devices from rooms for device table and network topology
  const allDevices = rooms.flatMap((room) =>
    (room.devices || []).map((device) => ({
      ...device,
      room_name: room.name,
      status: device.status || room.status,
      health: device.health || room.health,
    }))
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const totalRooms = healthSummary?.total_rooms || 0
  const availableRooms = healthSummary?.by_status?.Available || 0
  const inMeetingRooms = healthSummary?.by_status?.InMeeting || 0
  const offlineRooms = healthSummary?.by_status?.Offline || 0
  const networkHealth = offlineRooms === 0 ? 100 : Math.round(((totalRooms - offlineRooms) / totalRooms) * 100)

  return (
    <div className="space-y-6">
      {/* Status Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title="Total Rooms"
          value={totalRooms}
          icon={FiMonitor}
          color="primary"
          subtitle="Registered rooms"
        />
        <StatusCard
          title="Active Meetings"
          value={inMeetingRooms}
          icon={FiActivity}
          color="success"
          subtitle="Currently in use"
        />
        <StatusCard
          title="Network Health"
          value={`${networkHealth}%`}
          icon={FiCheckCircle}
          color={networkHealth > 90 ? 'success' : networkHealth > 70 ? 'warning' : 'danger'}
          subtitle="System operational"
        />
        <StatusCard
          title="Recent Alerts"
          value={mockAlerts.length}
          icon={FiAlertTriangle}
          color="warning"
          subtitle="Requires attention"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Network Topology */}
        <div className="lg:col-span-2">
          <NetworkTopology devices={allDevices.slice(0, 10)} onDeviceClick={handleDeviceClick} />
        </div>

        {/* Alerts Feed */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Recent Alerts</h3>
            <span className="text-xs text-gray-500">{mockAlerts.length} active</span>
          </div>
          <div className="space-y-3 max-h-[500px] overflow-y-auto scrollbar-thin">
            <AlertsList alerts={mockAlerts} />
          </div>
        </div>
      </div>

      {/* Mini Graphs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bandwidth Usage */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Bandwidth Usage (24h)
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={bandwidthData}>
              <defs>
                <linearGradient id="colorBandwidth" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#10b981"
                fillOpacity={1}
                fill="url(#colorBandwidth)"
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-between mt-4 text-sm">
            <span className="text-gray-400">Average: 62 Mbps</span>
            <span className="text-success-400">+5.2%</span>
          </div>
        </div>

        {/* Latency Trends */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Latency Trends (24h)
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-between mt-4 text-sm">
            <span className="text-gray-400">Average: 22ms</span>
            <span className="text-warning-400">+2.1ms</span>
          </div>
        </div>
      </div>

      {/* Recent Rooms */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Room Overview</h3>
          <button className="text-sm text-primary-500 hover:text-primary-400">
            View All →
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rooms.map((room) => (
            <RoomCard key={room.id} room={room} onClick={handleRoomClick} />
          ))}
        </div>
      </div>

      {/* Device List */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Network Devices</h3>
        <DeviceTable devices={allDevices.slice(0, 10)} onDeviceClick={handleDeviceClick} />
      </div>

      {/* Device Details Panel */}
      <DeviceDetailsPanel
        device={selectedDevice}
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
      />
    </div>
  )
}

export default Dashboard
