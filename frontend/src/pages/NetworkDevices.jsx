import React, { useState, useEffect } from 'react'
import { FiRefreshCw } from 'react-icons/fi'
import DeviceTable from '../components/UI/DeviceTable'
import NetworkTopology from '../components/UI/NetworkTopology'
import DeviceDetailsPanel from '../components/UI/DeviceDetailsPanel'
import { getRooms } from '../services/api'
import { toast } from 'react-toastify'

const NetworkDevices = () => {
  const [loading, setLoading] = useState(true)
  const [devices, setDevices] = useState([])
  const [selectedDevice, setSelectedDevice] = useState(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [viewMode, setViewMode] = useState('table') // 'table' or 'topology'

  useEffect(() => {
    fetchDevices()
    const interval = setInterval(fetchDevices, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchDevices = async () => {
    try {
      setLoading(true)
      const response = await getRooms(true)
      const rooms = response.data.data

      // Extract all devices from rooms
      const allDevices = rooms.flatMap((room) =>
        (room.devices || []).map((device) => ({
          ...device,
          room_id: room.id,
          room_name: room.name,
          status: device.status || room.status,
          health: device.health || room.health,
          last_seen: device.last_seen || room.last_started_time,
        }))
      )

      setDevices(allDevices)
    } catch (error) {
      console.error('Failed to fetch devices:', error)
      toast.error('Failed to load devices')
    } finally {
      setLoading(false)
    }
  }

  const handleDeviceClick = (device) => {
    setSelectedDevice(device)
    setIsPanelOpen(true)
  }

  const handleRefresh = () => {
    fetchDevices()
    toast.info('Refreshing device data...')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading network devices...</p>
        </div>
      </div>
    )
  }

  const deviceStats = {
    total: devices.length,
    online: devices.filter((d) => d.status?.toLowerCase() === 'available' || d.status?.toLowerCase() === 'online').length,
    warning: devices.filter((d) => d.status?.toLowerCase() === 'warning').length,
    offline: devices.filter((d) => d.status?.toLowerCase() === 'offline').length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Network Devices</h2>
          <p className="text-gray-400">{devices.length} devices detected</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setViewMode('table')}
            className={`btn ${viewMode === 'table' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Table View
          </button>
          <button
            onClick={() => setViewMode('topology')}
            className={`btn ${viewMode === 'topology' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Topology View
          </button>
          <button onClick={handleRefresh} className="btn btn-secondary">
            <FiRefreshCw className="mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-sm text-gray-400 mb-1">Total Devices</p>
          <p className="text-3xl font-bold text-white">{deviceStats.total}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-400 mb-1">Online</p>
          <p className="text-3xl font-bold text-success-400">{deviceStats.online}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-400 mb-1">Warning</p>
          <p className="text-3xl font-bold text-warning-400">{deviceStats.warning}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-400 mb-1">Offline</p>
          <p className="text-3xl font-bold text-danger-400">{deviceStats.offline}</p>
        </div>
      </div>

      {/* Content */}
      {viewMode === 'table' ? (
        <DeviceTable devices={devices} onDeviceClick={handleDeviceClick} />
      ) : (
        <NetworkTopology devices={devices} onDeviceClick={handleDeviceClick} />
      )}

      {/* Device Details Panel */}
      <DeviceDetailsPanel
        device={selectedDevice}
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
      />
    </div>
  )
}

export default NetworkDevices
