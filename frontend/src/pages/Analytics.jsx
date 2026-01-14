import React, { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { getUtilizationSummary, getRoomRanking, getUtilizationHeatmap } from '../services/api'
import { toast } from 'react-toastify'
import { motion } from 'framer-motion'

const Analytics = () => {
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState('30') // days
  const [utilizationData, setUtilizationData] = useState(null)
  const [rankingData, setRankingData] = useState([])
  const [heatmapData, setHeatmapData] = useState([])

  // Mock data for demonstration
  const utilizationByDayData = [
    { day: 'Mon', utilization: 75, meetings: 42 },
    { day: 'Tue', utilization: 82, meetings: 48 },
    { day: 'Wed', utilization: 88, meetings: 52 },
    { day: 'Thu', utilization: 85, meetings: 50 },
    { day: 'Fri', utilization: 78, meetings: 45 },
    { day: 'Sat', utilization: 35, meetings: 18 },
    { day: 'Sun', utilization: 28, meetings: 12 },
  ]

  const statusDistributionData = [
    { name: 'Available', value: 45, color: '#10b981' },
    { name: 'In Meeting', value: 30, color: '#3b82f6' },
    { name: 'Offline', value: 15, color: '#ef4444' },
    { name: 'Maintenance', value: 10, color: '#f59e0b' },
  ]

  const peakHoursData = [
    { hour: '8 AM', usage: 25 },
    { hour: '9 AM', usage: 65 },
    { hour: '10 AM', usage: 85 },
    { hour: '11 AM', usage: 90 },
    { hour: '12 PM', usage: 75 },
    { hour: '1 PM', usage: 70 },
    { hour: '2 PM', usage: 88 },
    { hour: '3 PM', usage: 82 },
    { hour: '4 PM', usage: 70 },
    { hour: '5 PM', usage: 45 },
  ]

  useEffect(() => {
    fetchAnalyticsData()
  }, [dateRange])

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true)
      const toDate = new Date().toISOString().split('T')[0]
      const fromDate = new Date(Date.now() - dateRange * 24 * 60 * 60 * 1000)
        .toISOString()
        .split('T')[0]

      const [utilizationRes, rankingRes, heatmapRes] = await Promise.all([
        getUtilizationSummary(fromDate, toDate),
        getRoomRanking(fromDate, toDate),
        getUtilizationHeatmap(fromDate, toDate),
      ])

      setUtilizationData(utilizationRes.data.data)
      setRankingData(rankingRes.data.data.slice(0, 10))
      setHeatmapData(heatmapRes.data.data)
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
      toast.error('Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Analytics</h2>
          <p className="text-gray-400">Room utilization and performance insights</p>
        </div>
        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          className="input"
        >
          <option value="7">Last 7 Days</option>
          <option value="30">Last 30 Days</option>
          <option value="90">Last 90 Days</option>
        </select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <p className="text-sm text-gray-400 mb-2">Average Utilization</p>
          <p className="text-4xl font-bold text-white mb-1">73%</p>
          <p className="text-sm text-success-400">+5.2% from last period</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6"
        >
          <p className="text-sm text-gray-400 mb-2">Total Meetings</p>
          <p className="text-4xl font-bold text-white mb-1">1,247</p>
          <p className="text-sm text-success-400">+12.4% from last period</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <p className="text-sm text-gray-400 mb-2">Peak Hour</p>
          <p className="text-4xl font-bold text-white mb-1">11 AM</p>
          <p className="text-sm text-gray-400">90% utilization</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6"
        >
          <p className="text-sm text-gray-400 mb-2">No-Show Rate</p>
          <p className="text-4xl font-bold text-white mb-1">8.2%</p>
          <p className="text-sm text-danger-400">+1.3% from last period</p>
        </motion.div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Utilization by Day */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Weekly Utilization Trend
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={utilizationByDayData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="day" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Bar dataKey="utilization" fill="#3b82f6" name="Utilization %" />
              <Bar dataKey="meetings" fill="#10b981" name="Meetings" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Room Status Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusDistributionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {statusDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Peak Hours */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Peak Usage Hours
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={peakHoursData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="hour" stroke="#9ca3af" />
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
                dataKey="usage"
                stroke="#f59e0b"
                strokeWidth={3}
                dot={{ fill: '#f59e0b' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Room Ranking */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Top Utilized Rooms
          </h3>
          <div className="space-y-3">
            {rankingData.length > 0 ? (
              rankingData.map((room, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-dark-800 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center text-white font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">
                        {room.room_name || `Room ${index + 1}`}
                      </p>
                      <p className="text-xs text-gray-500">
                        {room.total_meetings || 0} meetings
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-white">
                      {room.utilization_rate || 0}%
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                No ranking data available
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Heatmap */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Room Utilization Heatmap
        </h3>
        <p className="text-gray-400 text-sm mb-4">
          Hourly utilization across all rooms
        </p>
        <div className="overflow-x-auto">
          <div className="grid grid-cols-24 gap-1 min-w-max">
            {Array.from({ length: 7 }, (_, day) =>
              Array.from({ length: 24 }, (_, hour) => {
                const utilization = Math.random() * 100
                const getColor = (val) => {
                  if (val > 80) return 'bg-danger-600'
                  if (val > 60) return 'bg-warning-600'
                  if (val > 40) return 'bg-success-600'
                  if (val > 20) return 'bg-primary-600'
                  return 'bg-dark-700'
                }
                return (
                  <div
                    key={`${day}-${hour}`}
                    className={`w-8 h-8 ${getColor(utilization)} rounded hover:scale-110 transition-transform cursor-pointer`}
                    title={`Day ${day + 1}, Hour ${hour}: ${utilization.toFixed(1)}%`}
                  />
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics
