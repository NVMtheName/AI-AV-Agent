import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Health check
export const healthCheck = () => api.get('/health')

// Zoom Rooms
export const getRooms = (detailed = false) =>
  api.get(`/zoom/rooms?detailed=${detailed}`)

export const getRoomDetail = (roomId) =>
  api.get(`/zoom/rooms/${roomId}`)

export const getRoomMetrics = (roomId, fromDate, toDate) =>
  api.get(`/zoom/rooms/${roomId}/metrics`, { params: { from_date: fromDate, to_date: toDate } })

export const getRoomEvents = (roomId, fromDate, toDate) =>
  api.get(`/zoom/rooms/${roomId}/events`, { params: { from_date: fromDate, to_date: toDate } })

export const getRoomIssues = (roomId, fromDate, toDate) =>
  api.get(`/zoom/rooms/${roomId}/issues`, { params: { from_date: fromDate, to_date: toDate } })

// Dashboard
export const getDashboard = () => api.get('/zoom/dashboard')

export const getHealthSummary = () => api.get('/zoom/health-summary')

// Utilization
export const getUtilizationSummary = (fromDate, toDate, roomId = null) =>
  api.get('/utilization/summary', {
    params: { from_date: fromDate, to_date: toDate, room_id: roomId }
  })

export const getRoomDailyUtilization = (roomId, fromDate, toDate) =>
  api.get(`/utilization/rooms/${roomId}/daily`, {
    params: { from_date: fromDate, to_date: toDate }
  })

export const getRoomHourlyUtilization = (roomId, fromDate, toDate) =>
  api.get(`/utilization/rooms/${roomId}/hourly`, {
    params: { from_date: fromDate, to_date: toDate }
  })

export const getUtilizationHeatmap = (fromDate, toDate, building = null) =>
  api.get('/utilization/heatmap', {
    params: { from_date: fromDate, to_date: toDate, building }
  })

export const getRoomRanking = (fromDate, toDate, building = null) =>
  api.get('/utilization/ranking', {
    params: { from_date: fromDate, to_date: toDate, building }
  })

export const getRecommendations = (roomId = null, priority = null) =>
  api.get('/utilization/recommendations', {
    params: { room_id: roomId, priority }
  })

// Locations
export const getLocations = (parentLocationId = null, locationType = null) =>
  api.get('/zoom/locations', {
    params: { parent_location_id: parentLocationId, location_type: locationType }
  })

export default api
