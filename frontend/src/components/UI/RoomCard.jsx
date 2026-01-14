import React from 'react'
import { motion } from 'framer-motion'
import { FiMonitor, FiActivity, FiUsers, FiClock } from 'react-icons/fi'

const RoomCard = ({ room, onClick }) => {
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'available':
        return 'status-healthy'
      case 'inmeeting':
        return 'bg-primary-900/30 text-primary-400 border border-primary-700/50'
      case 'offline':
        return 'status-offline'
      default:
        return 'status-warning'
    }
  }

  const getHealthColor = (health) => {
    switch (health?.toLowerCase()) {
      case 'good':
      case 'normal':
        return 'text-success-400'
      case 'warning':
        return 'text-warning-400'
      case 'critical':
        return 'text-danger-400'
      default:
        return 'text-gray-400'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      className="card card-hover p-6 cursor-pointer"
      onClick={() => onClick(room)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1">
            {room.name || 'Unknown Room'}
          </h3>
          <p className="text-sm text-gray-500">
            {room.location_id || 'No location'}
          </p>
        </div>
        <span className={`status-badge ${getStatusColor(room.status)}`}>
          {room.status || 'Unknown'}
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center space-x-2">
          <FiActivity className={`${getHealthColor(room.health)}`} />
          <div>
            <p className="text-xs text-gray-500">Health</p>
            <p className={`text-sm font-medium ${getHealthColor(room.health)}`}>
              {room.health || 'Unknown'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <FiMonitor className="text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">Devices</p>
            <p className="text-sm font-medium text-white">
              {room.devices?.length || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-4 border-t border-dark-800 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-1">
          <FiClock />
          <span>
            {room.last_started_time
              ? new Date(room.last_started_time).toLocaleDateString()
              : 'Never'}
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="w-2 h-2 rounded-full bg-success-500 animate-pulse"></span>
          <span>Live</span>
        </div>
      </div>
    </motion.div>
  )
}

export default RoomCard
