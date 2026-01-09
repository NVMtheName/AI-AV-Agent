// Zoom Room Dashboard JavaScript

const API_BASE = '/api/zoom';
let allRooms = [];
let healthSummary = {};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    setupEventListeners();
});

// Initialize dashboard
async function initializeDashboard() {
    try {
        await Promise.all([
            loadHealthSummary(),
            loadRooms()
        ]);
        updateLastRefreshTime();
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        showError('Failed to load dashboard data. Please check your Zoom API credentials.');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', () => {
        initializeDashboard();
    });

    // Search input
    document.getElementById('searchInput').addEventListener('input', (e) => {
        filterRooms(e.target.value, document.getElementById('statusFilter').value);
    });

    // Status filter
    document.getElementById('statusFilter').addEventListener('change', (e) => {
        filterRooms(document.getElementById('searchInput').value, e.target.value);
    });

    // Modal close button
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('roomModal').style.display = 'none';
    });

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('roomModal');
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Auto-refresh every 30 seconds
    setInterval(() => {
        initializeDashboard();
    }, 30000);
}

// Load health summary
async function loadHealthSummary() {
    try {
        const response = await fetch(`${API_BASE}/health-summary`);
        const result = await response.json();

        if (result.success) {
            healthSummary = result.data;
            updateSummaryCards(healthSummary);
            updateHealthGrid(healthSummary);
            updateAlerts(healthSummary);
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Failed to load health summary:', error);
        throw error;
    }
}

// Update summary cards
function updateSummaryCards(summary) {
    document.getElementById('totalRooms').textContent = summary.total_rooms || 0;
    document.getElementById('availableRooms').textContent = summary.by_status?.Available || 0;
    document.getElementById('inMeetingRooms').textContent = summary.by_status?.InMeeting || 0;
    document.getElementById('offlineRooms').textContent = summary.by_status?.Offline || 0;
}

// Update health grid
function updateHealthGrid(summary) {
    const healthGrid = document.getElementById('healthGrid');
    const healthData = summary.by_health || {};

    if (Object.keys(healthData).length === 0) {
        healthGrid.innerHTML = '<div class="loading">No health data available</div>';
        return;
    }

    healthGrid.innerHTML = '';

    for (const [status, count] of Object.entries(healthData)) {
        const healthClass = getHealthClass(status);
        const healthItem = document.createElement('div');
        healthItem.className = `health-item ${healthClass}`;
        healthItem.innerHTML = `
            <div class="health-label">${status}</div>
            <div class="health-value">${count}</div>
        `;
        healthGrid.appendChild(healthItem);
    }
}

// Update alerts section
function updateAlerts(summary) {
    const alertsSection = document.getElementById('alertsSection');
    const alertsList = document.getElementById('alertsList');

    const offlineRooms = summary.offline_rooms || [];
    const unhealthyRooms = summary.unhealthy_rooms || [];

    const totalAlerts = offlineRooms.length + unhealthyRooms.length;

    if (totalAlerts === 0) {
        alertsSection.style.display = 'none';
        return;
    }

    alertsSection.style.display = 'block';
    alertsList.innerHTML = '';

    // Add offline room alerts
    offlineRooms.forEach(room => {
        const alertItem = document.createElement('div');
        alertItem.className = 'alert-item';
        alertItem.innerHTML = `
            <div>
                <span class="alert-icon">⚠️</span>
                <strong>${room.name}</strong> is offline
                ${room.location ? `<span class="text-secondary"> - ${room.location}</span>` : ''}
            </div>
            <button class="action-btn" onclick="viewRoomDetails('${room.id}')">View Details</button>
        `;
        alertsList.appendChild(alertItem);
    });

    // Add unhealthy room alerts
    unhealthyRooms.forEach(room => {
        const alertItem = document.createElement('div');
        alertItem.className = 'alert-item';
        const icon = room.health === 'Critical' ? '🔴' : '⚠️';
        alertItem.innerHTML = `
            <div>
                <span class="alert-icon">${icon}</span>
                <strong>${room.name}</strong> - ${room.health} health status
            </div>
            <button class="action-btn" onclick="viewRoomDetails('${room.id}')">View Details</button>
        `;
        alertsList.appendChild(alertItem);
    });
}

// Load rooms
async function loadRooms() {
    try {
        const response = await fetch(`${API_BASE}/rooms?detailed=true`);
        const result = await response.json();

        if (result.success) {
            allRooms = result.data;
            displayRooms(allRooms);
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Failed to load rooms:', error);
        document.getElementById('roomsTableBody').innerHTML = `
            <tr><td colspan="8" class="loading">Error loading rooms: ${error.message}</td></tr>
        `;
        throw error;
    }
}

// Display rooms in table
function displayRooms(rooms) {
    const tbody = document.getElementById('roomsTableBody');

    if (rooms.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No rooms found</td></tr>';
        return;
    }

    tbody.innerHTML = '';

    rooms.forEach(room => {
        const row = document.createElement('tr');

        const status = room.status || 'Unknown';
        const statusClass = getStatusClass(status);
        const health = room.health || 'Unknown';
        const healthClass = getHealthClass(health);
        const devices = room.devices || [];
        const deviceCount = devices.length;
        const lastActive = room.last_started_time || 'N/A';

        row.innerHTML = `
            <td><span class="status-badge ${statusClass}">${formatStatus(status)}</span></td>
            <td><strong>${room.name || 'Unknown'}</strong></td>
            <td>${room.room_type || room.type || 'N/A'}</td>
            <td><span class="health-badge ${healthClass}">${health}</span></td>
            <td><span class="device-list">${room.location_id || 'N/A'}</span></td>
            <td><span class="device-list">${deviceCount} device${deviceCount !== 1 ? 's' : ''}</span></td>
            <td>${formatTimestamp(lastActive)}</td>
            <td><button class="action-btn" onclick="viewRoomDetails('${room.id}')">Details</button></td>
        `;

        tbody.appendChild(row);
    });
}

// Filter rooms
function filterRooms(searchTerm, statusFilter) {
    const filtered = allRooms.filter(room => {
        const matchesSearch = !searchTerm ||
            room.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            room.location_id?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesStatus = !statusFilter || room.status === statusFilter;

        return matchesSearch && matchesStatus;
    });

    displayRooms(filtered);
}

// View room details
async function viewRoomDetails(roomId) {
    const modal = document.getElementById('roomModal');
    const modalBody = document.getElementById('modalBody');
    const modalRoomName = document.getElementById('modalRoomName');

    modal.style.display = 'block';
    modalBody.innerHTML = '<div class="loading">Loading room details...</div>';

    try {
        const response = await fetch(`${API_BASE}/rooms/${roomId}`);
        const result = await response.json();

        if (result.success) {
            const room = result.data;
            modalRoomName.textContent = room.room_name || room.name || 'Room Details';

            modalBody.innerHTML = `
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">Status</div>
                        <div class="detail-value">
                            <span class="status-badge ${getStatusClass(room.status)}">${formatStatus(room.status)}</span>
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Health</div>
                        <div class="detail-value">
                            <span class="health-badge ${getHealthClass(room.health)}">${room.health || 'Unknown'}</span>
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Room Type</div>
                        <div class="detail-value">${room.type || 'N/A'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Calendar Integration</div>
                        <div class="detail-value">${room.calendar?.type || 'None'}</div>
                    </div>
                </div>

                <h3 style="margin: 24px 0 16px 0;">Devices</h3>
                <div id="devicesList"></div>

                <h3 style="margin: 24px 0 16px 0;">Additional Information</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">Room ID</div>
                        <div class="detail-value" style="font-size: 12px; word-break: break-all;">${room.id}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Location ID</div>
                        <div class="detail-value" style="font-size: 12px;">${room.location_id || 'N/A'}</div>
                    </div>
                </div>
            `;

            // Display devices
            const devicesList = document.getElementById('devicesList');
            const devices = room.devices || [];

            if (devices.length === 0) {
                devicesList.innerHTML = '<p style="color: var(--text-secondary);">No device information available</p>';
            } else {
                devices.forEach(device => {
                    const deviceCard = document.createElement('div');
                    deviceCard.className = 'device-card';
                    deviceCard.innerHTML = `
                        <div class="device-header">
                            <div class="device-name">${device.device_name || 'Unknown Device'}</div>
                            <div class="device-type">${device.device_type || 'N/A'}</div>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            ${device.model || 'Model unknown'}
                            ${device.status ? ` - Status: ${device.status}` : ''}
                        </div>
                    `;
                    devicesList.appendChild(deviceCard);
                });
            }
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Failed to load room details:', error);
        modalBody.innerHTML = `<div class="loading">Error loading room details: ${error.message}</div>`;
    }
}

// Helper functions
function getStatusClass(status) {
    const statusMap = {
        'Available': 'available',
        'InMeeting': 'in-meeting',
        'Offline': 'offline',
        'UnderConstruction': 'under-construction'
    };
    return statusMap[status] || 'offline';
}

function getHealthClass(health) {
    const healthMap = {
        'Good': 'good',
        'Normal': 'good',
        'Warning': 'warning',
        'Critical': 'critical'
    };
    return healthMap[health] || 'good';
}

function formatStatus(status) {
    const statusMap = {
        'InMeeting': 'In Meeting',
        'UnderConstruction': 'Under Construction'
    };
    return statusMap[status] || status;
}

function formatTimestamp(timestamp) {
    if (!timestamp || timestamp === 'N/A') return 'N/A';

    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        // Less than 1 hour ago
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }

        // Less than 24 hours ago
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }

        // More than 24 hours ago
        const days = Math.floor(diff / 86400000);
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;

        return date.toLocaleDateString();
    } catch (error) {
        return timestamp;
    }
}

function updateLastRefreshTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    document.getElementById('lastUpdated').textContent = timeString;
}

function showError(message) {
    const alertsSection = document.getElementById('alertsSection');
    const alertsList = document.getElementById('alertsList');

    alertsSection.style.display = 'block';
    alertsList.innerHTML = `
        <div class="alert-item">
            <div>
                <span class="alert-icon">❌</span>
                <strong>Error:</strong> ${message}
            </div>
        </div>
    `;
}
