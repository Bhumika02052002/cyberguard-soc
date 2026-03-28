import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import io from 'socket.io-client';
import { API_BASE_URL } from '../config';

const socket = io(API_BASE_URL);  // Use the backend URL from config

export default function AlertPanel() {
  const [alerts, setAlerts] = useState([]);

  const fetchAlerts = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/alerts`);
      setAlerts(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchAlerts();
    socket.on('new_alert', (alert) => {
      setAlerts(prev => [alert, ...prev]);
      toast.info(`New alert: ${alert.threat_type} - ${alert.severity}`);
    });
    return () => socket.off('new_alert');
  }, []);

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'Critical': return 'bg-red-700';
      case 'High': return 'bg-red-500';
      case 'Medium': return 'bg-yellow-500';
      default: return 'bg-blue-500';
    }
  };

  const handleBlacklist = async (ip) => {
    try {
      await axios.post(`${API_BASE_URL}/api/blacklist`, { ip, reason: 'Manual blacklist' });
      toast.success(`IP ${ip} blacklisted`);
    } catch (err) {
      toast.error('Failed to blacklist IP');
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">Alerts</h2>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.length === 0 && (
          <p className="text-gray-500 dark:text-gray-400">No alerts yet.</p>
        )}
        {alerts.map((alert) => (
          <div key={alert.id} className={`border-l-4 ${getSeverityColor(alert.severity)} p-3 rounded bg-gray-50 dark:bg-gray-700`}>
            <div className="flex justify-between items-start">
              <div>
                <p className="font-bold text-gray-800 dark:text-white">{alert.threat_type}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{new Date(alert.timestamp).toLocaleString()}</p>
                <p className="text-sm">IP: {alert.ip_address}</p>
                <p className="text-sm">{alert.description}</p>
              </div>
              <button
                onClick={() => handleBlacklist(alert.ip_address)}
                className="text-xs bg-gray-800 hover:bg-gray-900 text-white px-2 py-1 rounded"
              >
                Blacklist IP
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}