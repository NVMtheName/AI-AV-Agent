import React, { useState, useEffect } from 'react'
import { FiAlertTriangle, FiCheckCircle, FiFilter, FiDownload } from 'react-icons/fi'
import AlertsList from '../components/UI/AlertsList'
import { motion } from 'framer-motion'
import { toast } from 'react-toastify'

const Alerts = () => {
  const [alerts, setAlerts] = useState([])
  const [filteredAlerts, setFilteredAlerts] = useState([])
  const [severityFilter, setSeverityFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('active')

  // Mock alerts data
  const mockAlerts = [
    {
      id: 1,
      title: 'Device Offline',
      message: 'Zoom Room Controller in Conference Room A is not responding',
      severity: 'critical',
      source: 'Network Monitor',
      timestamp: new Date(Date.now() - 300000),
      room_name: 'Conference Room A',
      status: 'active',
    },
    {
      id: 2,
      title: 'High Latency Detected',
      message: 'Network latency exceeds threshold (45ms) in Building B',
      severity: 'warning',
      source: 'QoS Monitor',
      timestamp: new Date(Date.now() - 900000),
      room_name: 'Building B',
      status: 'active',
    },
    {
      id: 3,
      title: 'Firmware Update Available',
      message: 'New firmware version 5.2.1 available for 3 devices',
      severity: 'info',
      source: 'System',
      timestamp: new Date(Date.now() - 3600000),
      status: 'active',
    },
    {
      id: 4,
      title: 'Audio Quality Degraded',
      message: 'Poor audio quality detected in Meeting Room 202',
      severity: 'warning',
      source: 'QoS Monitor',
      timestamp: new Date(Date.now() - 7200000),
      room_name: 'Meeting Room 202',
      status: 'active',
    },
    {
      id: 5,
      title: 'Device Battery Low',
      message: 'Zoom Room Scheduler battery below 20% in Conference Room C',
      severity: 'warning',
      source: 'Device Monitor',
      timestamp: new Date(Date.now() - 10800000),
      room_name: 'Conference Room C',
      status: 'active',
    },
    {
      id: 6,
      title: 'Network Restored',
      message: 'Network connectivity restored for Conference Room A',
      severity: 'info',
      source: 'Network Monitor',
      timestamp: new Date(Date.now() - 14400000),
      room_name: 'Conference Room A',
      status: 'resolved',
    },
  ]

  useEffect(() => {
    setAlerts(mockAlerts)
  }, [])

  useEffect(() => {
    filterAlerts()
  }, [alerts, severityFilter, statusFilter])

  const filterAlerts = () => {
    let filtered = alerts

    // Severity filter
    if (severityFilter !== 'all') {
      filtered = filtered.filter((alert) => alert.severity === severityFilter)
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((alert) => alert.status === statusFilter)
    }

    setFilteredAlerts(filtered)
  }

  const handleDismiss = (alertId) => {
    setAlerts(alerts.map((alert) =>
      alert.id === alertId ? { ...alert, status: 'resolved' } : alert
    ))
    toast.success('Alert dismissed')
  }

  const handleDismissAll = () => {
    setAlerts(alerts.map((alert) => ({ ...alert, status: 'resolved' })))
    toast.success('All alerts dismissed')
  }

  const handleExport = () => {
    toast.info('Exporting alerts...')
    // Export logic here
  }

  const alertCounts = {
    all: alerts.length,
    critical: alerts.filter((a) => a.severity === 'critical' && a.status === 'active').length,
    warning: alerts.filter((a) => a.severity === 'warning' && a.status === 'active').length,
    info: alerts.filter((a) => a.severity === 'info' && a.status === 'active').length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Alerts & Notifications</h2>
          <p className="text-gray-400">
            {filteredAlerts.filter((a) => a.status === 'active').length} active alerts
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={handleExport} className="btn btn-secondary">
            <FiDownload className="mr-2" />
            Export
          </button>
          <button onClick={handleDismissAll} className="btn btn-danger">
            Dismiss All
          </button>
        </div>
      </div>

      {/* Alert Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Total Alerts</p>
            <FiAlertTriangle className="text-gray-400" />
          </div>
          <p className="text-4xl font-bold text-white">{alertCounts.all}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Critical</p>
            <FiAlertTriangle className="text-danger-400" />
          </div>
          <p className="text-4xl font-bold text-danger-400">{alertCounts.critical}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Warning</p>
            <FiAlertTriangle className="text-warning-400" />
          </div>
          <p className="text-4xl font-bold text-warning-400">{alertCounts.warning}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Info</p>
            <FiCheckCircle className="text-primary-400" />
          </div>
          <p className="text-4xl font-bold text-primary-400">{alertCounts.info}</p>
        </motion.div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex items-center space-x-2 flex-1">
            <FiFilter className="text-gray-400" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="input flex-1"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
          <div className="flex items-center space-x-2 flex-1">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input flex-1"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      {filteredAlerts.length > 0 ? (
        <AlertsList alerts={filteredAlerts} onDismiss={handleDismiss} />
      ) : (
        <div className="card p-12 text-center">
          <FiCheckCircle className="text-6xl text-success-500 mx-auto mb-4" />
          <p className="text-xl text-white mb-2">No alerts found</p>
          <p className="text-gray-500">All systems are running smoothly</p>
        </div>
      )}
    </div>
  )
}

export default Alerts
