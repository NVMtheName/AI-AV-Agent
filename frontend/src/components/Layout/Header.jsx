import React, { useState, useEffect } from 'react'
import { FiSearch, FiBell, FiUser, FiRefreshCw } from 'react-icons/fi'
import { useLocation } from 'react-router-dom'

const Header = () => {
  const location = useLocation()
  const [searchQuery, setSearchQuery] = useState('')
  const [notifications, setNotifications] = useState(3)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const getBreadcrumb = () => {
    const path = location.pathname
    if (path === '/') return 'Dashboard'
    return path.substring(1).replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const handleRefresh = () => {
    setIsRefreshing(true)
    // Trigger refresh logic here
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  return (
    <header className="h-16 bg-dark-900 border-b border-dark-800 flex items-center justify-between px-6">
      {/* Breadcrumb */}
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-semibold">{getBreadcrumb()}</h1>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <span>{currentTime.toLocaleDateString()}</span>
          <span>•</span>
          <span>{currentTime.toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center space-x-4">
        {/* Search */}
        <div className="relative">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-dark-800 border border-dark-700 rounded-lg pl-10 pr-4 py-2 w-64 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
          />
        </div>

        {/* Refresh Button */}
        <button
          onClick={handleRefresh}
          className={`p-2 hover:bg-dark-800 rounded-lg transition-all ${
            isRefreshing ? 'animate-spin' : ''
          }`}
        >
          <FiRefreshCw className="text-gray-400" />
        </button>

        {/* Notifications */}
        <button className="relative p-2 hover:bg-dark-800 rounded-lg transition-colors">
          <FiBell className="text-gray-400" />
          {notifications > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-danger-500 text-white text-xs rounded-full flex items-center justify-center">
              {notifications}
            </span>
          )}
        </button>

        {/* User Profile */}
        <button className="flex items-center space-x-2 hover:bg-dark-800 rounded-lg px-3 py-2 transition-colors">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center">
            <FiUser className="text-white text-sm" />
          </div>
        </button>
      </div>
    </header>
  )
}

export default Header
