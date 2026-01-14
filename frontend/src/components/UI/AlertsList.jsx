import React from 'react'
import { motion } from 'framer-motion'
import { FiAlertTriangle, FiAlertCircle, FiInfo, FiX } from 'react-icons/fi'

const AlertsList = ({ alerts, onDismiss }) => {
  const getAlertIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return <FiAlertTriangle className="text-danger-500" />
      case 'warning':
        return <FiAlertCircle className="text-warning-500" />
      default:
        return <FiInfo className="text-primary-500" />
    }
  }

  const getAlertBorder = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'border-l-danger-500'
      case 'warning':
        return 'border-l-warning-500'
      default:
        return 'border-l-primary-500'
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="space-y-3">
      {alerts && alerts.length > 0 ? (
        alerts.map((alert, index) => (
          <motion.div
            key={alert.id || index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ delay: index * 0.05 }}
            className={`card p-4 border-l-4 ${getAlertBorder(alert.severity)} hover:shadow-xl transition-shadow`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <div className="mt-1">{getAlertIcon(alert.severity)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h4 className="text-sm font-semibold text-white">
                      {alert.title || 'Alert'}
                    </h4>
                    <span
                      className={`status-badge ${
                        alert.severity?.toLowerCase() === 'critical'
                          ? 'status-critical'
                          : alert.severity?.toLowerCase() === 'warning'
                          ? 'status-warning'
                          : 'bg-primary-900/30 text-primary-400 border border-primary-700/50'
                      }`}
                    >
                      {alert.severity || 'Info'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">
                    {alert.message || 'No message available'}
                  </p>
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>{alert.source || 'System'}</span>
                    <span>•</span>
                    <span>{formatTimestamp(alert.timestamp || new Date())}</span>
                    {alert.room_name && (
                      <>
                        <span>•</span>
                        <span>{alert.room_name}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              {onDismiss && (
                <button
                  onClick={() => onDismiss(alert.id)}
                  className="ml-3 p-1 hover:bg-dark-800 rounded transition-colors"
                >
                  <FiX className="text-gray-500" />
                </button>
              )}
            </div>
          </motion.div>
        ))
      ) : (
        <div className="card p-8 text-center">
          <FiInfo className="text-4xl text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500">No alerts at this time</p>
          <p className="text-sm text-gray-600 mt-1">All systems operational</p>
        </div>
      )}
    </div>
  )
}

export default AlertsList
