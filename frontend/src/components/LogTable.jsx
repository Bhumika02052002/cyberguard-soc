import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { API_BASE_URL } from '../config';  // new import

export default function LogTable() {
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState({ ip: '', event_type: '', status: '' });

  const fetchLogs = async () => {
    try {
      const params = {};
      if (filter.ip) params.ip = filter.ip;
      if (filter.event_type) params.event_type = filter.event_type;
      if (filter.status) params.status = filter.status;
      const res = await axios.get(`${API_BASE_URL}/api/logs`, { params });
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filter]);

  const handleManualThreat = async (logId) => {
    try {
      await axios.post(`${API_BASE_URL}/api/manual-threat`, { log_id: logId });
      toast.success('Manual threat alert created');
    } catch (err) {
      toast.error('Failed to create alert');
    }
  };

  const exportCSV = async () => {
    window.location.href = `${API_BASE_URL}/api/export/csv`;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-800 dark:text-white">Logs</h2>
        <div className="flex space-x-2">
          <button
            onClick={exportCSV}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
          >
            Export CSV
          </button>
          <input
            type="text"
            placeholder="Filter by IP"
            className="px-2 py-1 border rounded dark:bg-gray-700 dark:text-white"
            value={filter.ip}
            onChange={(e) => setFilter({ ...filter, ip: e.target.value })}
          />
          <select
            className="px-2 py-1 border rounded dark:bg-gray-700 dark:text-white"
            value={filter.event_type}
            onChange={(e) => setFilter({ ...filter, event_type: e.target.value })}
          >
            <option value="">All Events</option>
            <option value="login">Login</option>
            <option value="file_access">File Access</option>
            <option value="network">Network</option>
          </select>
          <select
            className="px-2 py-1 border rounded dark:bg-gray-700 dark:text-white"
            value={filter.status}
            onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          >
            <option value="">All Status</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Timestamp</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">IP</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Port</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Event</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Country</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{log.ip_address}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{log.port}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    log.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {log.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{log.event_type}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{log.country || 'N/A'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button
                    onClick={() => handleManualThreat(log.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Mark as Threat
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}