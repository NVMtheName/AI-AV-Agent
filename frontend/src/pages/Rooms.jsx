import React, { useState, useEffect } from 'react'
import { FiGrid, FiList, FiFilter } from 'react-icons/fi'
import RoomCard from '../components/UI/RoomCard'
import { getRooms, getRoomDetail } from '../services/api'
import { toast } from 'react-toastify'
import { motion } from 'framer-motion'
import DeviceDetailsPanel from '../components/UI/DeviceDetailsPanel'

const Rooms = () => {
  const [loading, setLoading] = useState(true)
  const [rooms, setRooms] = useState([])
  const [filteredRooms, setFilteredRooms] = useState([])
  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'list'
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedRoom, setSelectedRoom] = useState(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)

  useEffect(() => {
    fetchRooms()
    const interval = setInterval(fetchRooms, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    filterRooms()
  }, [rooms, searchQuery, statusFilter])

  const fetchRooms = async () => {
    try {
      setLoading(true)
      const response = await getRooms(true)
      setRooms(response.data.data)
    } catch (error) {
      console.error('Failed to fetch rooms:', error)
      toast.error('Failed to load rooms')
    } finally {
      setLoading(false)
    }
  }

  const filterRooms = () => {
    let filtered = rooms

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (room) =>
          room.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          room.location_id?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((room) => room.status === statusFilter)
    }

    setFilteredRooms(filtered)
  }

  const handleRoomClick = async (room) => {
    try {
      const response = await getRoomDetail(room.id)
      setSelectedRoom(response.data.data)
      setIsPanelOpen(true)
    } catch (error) {
      console.error('Failed to fetch room details:', error)
      toast.error('Failed to load room details')
    }
  }

  const statusCounts = {
    all: rooms.length,
    Available: rooms.filter((r) => r.status === 'Available').length,
    InMeeting: rooms.filter((r) => r.status === 'InMeeting').length,
    Offline: rooms.filter((r) => r.status === 'Offline').length,
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading rooms...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Zoom Rooms</h2>
          <p className="text-gray-400">
            {filteredRooms.length} of {rooms.length} rooms
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg transition-colors ${
              viewMode === 'grid'
                ? 'bg-primary-600 text-white'
                : 'bg-dark-800 text-gray-400 hover:text-white'
            }`}
          >
            <FiGrid />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg transition-colors ${
              viewMode === 'list'
                ? 'bg-primary-600 text-white'
                : 'bg-dark-800 text-gray-400 hover:text-white'
            }`}
          >
            <FiList />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <input
            type="text"
            placeholder="Search rooms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input flex-1"
          />

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <FiFilter className="text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input min-w-[200px]"
            >
              <option value="all">All Status ({statusCounts.all})</option>
              <option value="Available">Available ({statusCounts.Available})</option>
              <option value="InMeeting">In Meeting ({statusCounts.InMeeting})</option>
              <option value="Offline">Offline ({statusCounts.Offline})</option>
            </select>
          </div>
        </div>
      </div>

      {/* Rooms Grid/List */}
      {filteredRooms.length > 0 ? (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
              : 'space-y-4'
          }
        >
          {filteredRooms.map((room, index) => (
            <motion.div
              key={room.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <RoomCard room={room} onClick={handleRoomClick} />
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <p className="text-gray-500 text-lg">No rooms found</p>
          <p className="text-gray-600 text-sm mt-2">
            Try adjusting your filters or search query
          </p>
        </div>
      )}

      {/* Room Details Panel */}
      <DeviceDetailsPanel
        device={selectedRoom}
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
      />
    </div>
  )
}

export default Rooms
