import React from 'react'
import { motion } from 'framer-motion'

const StatusCard = ({ title, value, icon: Icon, color = 'primary', subtitle, trend }) => {
  const colorClasses = {
    primary: 'from-primary-600 to-primary-700',
    success: 'from-success-600 to-success-700',
    warning: 'from-warning-600 to-warning-700',
    danger: 'from-danger-600 to-danger-700',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="card card-hover p-6"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-2">
            {title}
          </p>
          <div className="flex items-baseline space-x-2">
            <h3 className="text-4xl font-bold text-white">{value}</h3>
            {trend && (
              <span
                className={`text-sm font-medium ${
                  trend > 0 ? 'text-success-400' : 'text-danger-400'
                }`}
              >
                {trend > 0 ? '+' : ''}
                {trend}%
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-2">{subtitle}</p>
          )}
        </div>
        <div
          className={`w-14 h-14 bg-gradient-to-br ${colorClasses[color]} rounded-xl flex items-center justify-center shadow-lg`}
        >
          <Icon className="text-white text-2xl" />
        </div>
      </div>
    </motion.div>
  )
}

export default StatusCard
