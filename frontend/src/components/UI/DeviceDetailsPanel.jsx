import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FiX, FiActivity, FiClock, FiWifi, FiServer } from 'react-icons/fi'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const DeviceDetailsPanel = ({ device, isOpen, onClose }) => {
  // Mock performance data
  const performanceData = [
    { time: '00:00', latency: 12, bandwidth: 85 },
    { time: '04:00', latency: 15, bandwidth: 78 },
    { time: '08:00', latency: 28, bandwidth: 92 },
    { time: '12:00', latency: 35, bandwidth: 95 },
    { time: '16:00', latency: 32, bandwidth: 88 },
    { time: '20:00', latency: 18, bandwidth: 80 },
  ]

  if (!device) return null

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-full max-w-2xl bg-dark-900 shadow-2xl z-50 overflow-y-auto scrollbar-thin"
          >
            {/* Header */}
            <div className="sticky top-0 bg-dark-900 border-b border-dark-800 p-6 flex items-start justify-between z-10">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">
                  {device.device_name || device.name || 'Unknown Device'}
                </h2>
                <p className="text-gray-400">
                  {device.device_type || device.type || 'Unknown Type'}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
              >
                <FiX className="text-xl text-gray-400" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Status Overview */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Status Overview</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Current Status</p>
                    <span
                      className={`status-badge ${
                        device.status?.toLowerCase() === 'available' || device.status?.toLowerCase() === 'online'
                          ? 'status-healthy'
                          : device.status?.toLowerCase() === 'warning'
                          ? 'status-warning'
                          : 'status-critical'
                      }`}
                    >
                      {device.status || 'Unknown'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Health</p>
                    <span className="text-white font-medium">
                      {device.health || 'Unknown'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">IP Address</p>
                    <span className="text-white font-medium flex items-center">
                      <FiWifi className="mr-2 text-gray-400" />
                      {device.ip_address || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Model</p>
                    <span className="text-white font-medium">
                      {device.model || 'Unknown'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Device Information */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Device Information</h3>
                <div className="space-y-3">
                  <div className="flex justify-between py-2 border-b border-dark-800">
                    <span className="text-gray-400">Device ID</span>
                    <span className="text-white font-mono text-sm">
                      {device.id || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-dark-800">
                    <span className="text-gray-400">Room</span>
                    <span className="text-white">{device.room_name || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-dark-800">
                    <span className="text-gray-400">Last Seen</span>
                    <span className="text-white flex items-center">
                      <FiClock className="mr-2 text-gray-400" />
                      {device.last_seen
                        ? new Date(device.last_seen).toLocaleString()
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-gray-400">Firmware</span>
                    <span className="text-white">{device.firmware || 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Performance Metrics (24h)
                </h3>
                <div className="space-y-6">
                  {/* Latency Chart */}
                  <div>
                    <p className="text-sm text-gray-400 mb-3">Latency (ms)</p>
                    <ResponsiveContainer width="100%" height={150}>
                      <LineChart data={performanceData}>
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
                          dataKey="latency"
                          stroke="#f59e0b"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Bandwidth Chart */}
                  <div>
                    <p className="text-sm text-gray-400 mb-3">Bandwidth Usage (%)</p>
                    <ResponsiveContainer width="100%" height={150}>
                      <LineChart data={performanceData}>
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
                          dataKey="bandwidth"
                          stroke="#10b981"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Recent Alerts */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Recent Alerts</h3>
                <div className="space-y-3">
                  {device.recent_alerts && device.recent_alerts.length > 0 ? (
                    device.recent_alerts.map((alert, index) => (
                      <div
                        key={index}
                        className="flex items-start space-x-3 p-3 bg-dark-800 rounded-lg"
                      >
                        <FiActivity className="text-warning-500 mt-1" />
                        <div className="flex-1">
                          <p className="text-sm text-white">{alert.message}</p>
                          <p className="text-xs text-gray-500 mt-1">{alert.timestamp}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-4">No recent alerts</p>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex space-x-3">
                <button className="btn btn-primary flex-1">
                  <FiActivity className="mr-2" />
                  Run Diagnostics
                </button>
                <button className="btn btn-secondary flex-1">
                  <FiServer className="mr-2" />
                  Restart Device
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default DeviceDetailsPanel
