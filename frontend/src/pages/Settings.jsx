import React, { useState } from 'react'
import { FiSave, FiRefreshCw, FiBell, FiMonitor, FiShield, FiDatabase } from 'react-icons/fi'
import { toast } from 'react-toastify'
import { motion } from 'framer-motion'

const Settings = () => {
  const [settings, setSettings] = useState({
    // General Settings
    refreshInterval: '30',
    theme: 'dark',
    timezone: 'UTC',

    // Notification Settings
    emailNotifications: true,
    slackNotifications: false,
    criticalAlerts: true,
    warningAlerts: true,
    infoAlerts: false,

    // Monitoring Settings
    healthCheckInterval: '60',
    performanceMonitoring: true,
    networkScanning: true,
    autoDiscovery: true,

    // Display Settings
    defaultView: 'grid',
    itemsPerPage: '20',
    showDeviceDetails: true,

    // Advanced Settings
    dataRetention: '90',
    logLevel: 'info',
    apiTimeout: '30',
  })

  const handleChange = (field, value) => {
    setSettings({ ...settings, [field]: value })
  }

  const handleSave = () => {
    // Save settings logic here
    toast.success('Settings saved successfully!')
  }

  const handleReset = () => {
    toast.info('Settings reset to defaults')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Settings</h2>
          <p className="text-gray-400">Configure your dashboard preferences</p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={handleReset} className="btn btn-secondary">
            <FiRefreshCw className="mr-2" />
            Reset
          </button>
          <button onClick={handleSave} className="btn btn-primary">
            <FiSave className="mr-2" />
            Save Changes
          </button>
        </div>
      </div>

      {/* General Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-6"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
            <FiMonitor className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">General Settings</h3>
            <p className="text-sm text-gray-400">Basic dashboard configuration</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Refresh Interval (seconds)
              </label>
              <input
                type="number"
                value={settings.refreshInterval}
                onChange={(e) => handleChange('refreshInterval', e.target.value)}
                className="input w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Theme
              </label>
              <select
                value={settings.theme}
                onChange={(e) => handleChange('theme', e.target.value)}
                className="input w-full"
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
                <option value="auto">Auto</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Timezone
              </label>
              <select
                value={settings.timezone}
                onChange={(e) => handleChange('timezone', e.target.value)}
                className="input w-full"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
                <option value="Europe/London">London</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Default View
              </label>
              <select
                value={settings.defaultView}
                onChange={(e) => handleChange('defaultView', e.target.value)}
                className="input w-full"
              >
                <option value="grid">Grid View</option>
                <option value="list">List View</option>
                <option value="table">Table View</option>
              </select>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Notification Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card p-6"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-warning-600 rounded-lg flex items-center justify-center">
            <FiBell className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Notification Settings</h3>
            <p className="text-sm text-gray-400">Configure alert preferences</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-dark-800 rounded-lg">
            <div>
              <p className="text-white font-medium">Email Notifications</p>
              <p className="text-sm text-gray-400">Receive alerts via email</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.emailNotifications}
                onChange={(e) => handleChange('emailNotifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-dark-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-dark-800 rounded-lg">
            <div>
              <p className="text-white font-medium">Slack Notifications</p>
              <p className="text-sm text-gray-400">Send alerts to Slack channel</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.slackNotifications}
                onChange={(e) => handleChange('slackNotifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-dark-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="space-y-3 p-4 bg-dark-800 rounded-lg">
            <p className="text-white font-medium mb-3">Alert Types</p>
            <div className="space-y-2">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings.criticalAlerts}
                  onChange={(e) => handleChange('criticalAlerts', e.target.checked)}
                  className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-600"
                />
                <span className="text-gray-300">Critical Alerts</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings.warningAlerts}
                  onChange={(e) => handleChange('warningAlerts', e.target.checked)}
                  className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-600"
                />
                <span className="text-gray-300">Warning Alerts</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings.infoAlerts}
                  onChange={(e) => handleChange('infoAlerts', e.target.checked)}
                  className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-600"
                />
                <span className="text-gray-300">Info Alerts</span>
              </label>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Monitoring Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card p-6"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-success-600 rounded-lg flex items-center justify-center">
            <FiShield className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Monitoring Settings</h3>
            <p className="text-sm text-gray-400">Configure monitoring behavior</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Health Check Interval (seconds)
            </label>
            <input
              type="number"
              value={settings.healthCheckInterval}
              onChange={(e) => handleChange('healthCheckInterval', e.target.value)}
              className="input w-full"
            />
          </div>
          <div className="flex items-center space-x-3 p-4 bg-dark-800 rounded-lg">
            <input
              type="checkbox"
              checked={settings.performanceMonitoring}
              onChange={(e) => handleChange('performanceMonitoring', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-600"
            />
            <div>
              <p className="text-white font-medium">Performance Monitoring</p>
              <p className="text-xs text-gray-400">Track device performance metrics</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-4 bg-dark-800 rounded-lg">
            <input
              type="checkbox"
              checked={settings.networkScanning}
              onChange={(e) => handleChange('networkScanning', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-600"
            />
            <div>
              <p className="text-white font-medium">Network Scanning</p>
              <p className="text-xs text-gray-400">Continuously scan network for devices</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-4 bg-dark-800 rounded-lg">
            <input
              type="checkbox"
              checked={settings.autoDiscovery}
              onChange={(e) => handleChange('autoDiscovery', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-600"
            />
            <div>
              <p className="text-white font-medium">Auto Discovery</p>
              <p className="text-xs text-gray-400">Automatically discover new devices</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Advanced Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card p-6"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-danger-600 rounded-lg flex items-center justify-center">
            <FiDatabase className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Advanced Settings</h3>
            <p className="text-sm text-gray-400">Advanced configuration options</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Data Retention (days)
            </label>
            <input
              type="number"
              value={settings.dataRetention}
              onChange={(e) => handleChange('dataRetention', e.target.value)}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Log Level
            </label>
            <select
              value={settings.logLevel}
              onChange={(e) => handleChange('logLevel', e.target.value)}
              className="input w-full"
            >
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              API Timeout (seconds)
            </label>
            <input
              type="number"
              value={settings.apiTimeout}
              onChange={(e) => handleChange('apiTimeout', e.target.value)}
              className="input w-full"
            />
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default Settings
