import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { FiServer, FiActivity, FiClock, FiWifi } from 'react-icons/fi'

const DeviceTable = ({ devices, onDeviceClick }) => {
  const [sortField, setSortField] = useState('name')
  const [sortDirection, setSortDirection] = useState('asc')

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedDevices = [...devices].sort((a, b) => {
    const aVal = a[sortField] || ''
    const bVal = b[sortField] || ''
    if (sortDirection === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'online':
      case 'available':
        return 'status-healthy'
      case 'warning':
        return 'status-warning'
      case 'offline':
      case 'critical':
        return 'status-critical'
      default:
        return 'status-offline'
    }
  }

  const formatUptime = (lastSeen) => {
    if (!lastSeen) return 'N/A'
    const diff = Date.now() - new Date(lastSeen).getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    return `${days}d ${hours}h`
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-dark-800 border-b border-dark-700">
            <tr>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300"
                onClick={() => handleSort('name')}
              >
                Device Name
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300"
                onClick={() => handleSort('type')}
              >
                Type
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300"
                onClick={() => handleSort('ip_address')}
              >
                IP Address
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Uptime
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Last Seen
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-800">
            {sortedDevices.map((device, index) => (
              <motion.tr
                key={device.id || index}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.05 }}
                className="hover:bg-dark-800 cursor-pointer transition-colors"
                onClick={() => onDeviceClick(device)}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <FiServer className="text-gray-400 mr-3" />
                    <div>
                      <div className="text-sm font-medium text-white">
                        {device.device_name || device.name || 'Unknown'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {device.model || 'N/A'}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-300">
                    {device.device_type || device.type || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <FiWifi className="text-gray-500 mr-2" />
                    <span className="text-sm text-gray-300">
                      {device.ip_address || 'N/A'}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`status-badge ${getStatusColor(device.status)}`}>
                    {device.status || 'Unknown'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatUptime(device.last_seen)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-500">
                    <FiClock className="mr-2" />
                    {device.last_seen
                      ? new Date(device.last_seen).toLocaleString()
                      : 'N/A'}
                  </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default DeviceTable
