import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  FiHome, FiMonitor, FiActivity, FiBarChart2,
  FiBell, FiSettings, FiChevronLeft, FiChevronRight
} from 'react-icons/fi'
import { HiOutlineServerStack } from 'react-icons/hi2'

const Sidebar = ({ collapsed, setCollapsed }) => {
  const menuItems = [
    { path: '/', icon: FiHome, label: 'Dashboard' },
    { path: '/rooms', icon: FiMonitor, label: 'Rooms' },
    { path: '/network-devices', icon: HiOutlineServerStack, label: 'Network Devices' },
    { path: '/analytics', icon: FiBarChart2, label: 'Analytics' },
    { path: '/alerts', icon: FiBell, label: 'Alerts' },
    { path: '/settings', icon: FiSettings, label: 'Settings' },
  ]

  return (
    <aside
      className={`${
        collapsed ? 'w-20' : 'w-64'
      } bg-dark-900 border-r border-dark-800 transition-all duration-300 flex flex-col`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-dark-800">
        {!collapsed && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
              <FiActivity className="text-white text-lg" />
            </div>
            <span className="font-bold text-lg">AI-AV Agent</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
        >
          {collapsed ? <FiChevronRight /> : <FiChevronLeft />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto scrollbar-thin">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-3 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-primary-600 text-white shadow-lg'
                  : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'
              }`
            }
          >
            <item.icon className="text-xl flex-shrink-0" />
            {!collapsed && <span className="font-medium">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-dark-800">
        {!collapsed ? (
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-success-500 to-success-700 rounded-full flex items-center justify-center text-white font-semibold">
              AV
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">AV Admin</p>
              <p className="text-xs text-gray-500 truncate">System Online</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-10 h-10 bg-gradient-to-br from-success-500 to-success-700 rounded-full flex items-center justify-center text-white font-semibold">
              AV
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}

export default Sidebar
