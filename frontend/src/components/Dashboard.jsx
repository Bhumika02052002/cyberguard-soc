import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { API_BASE_URL } from '../config';
import Charts from './Charts';
import AlertPanel from './AlertPanel';
import LogTable from './LogTable';

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_logs: 0,
    total_alerts: 0,
    failed_logins: 0,
    successful_logins: 0,
    alerts_per_type: {},
    hourly_traffic: []
  });
  const [securityLevel, setSecurityLevel] = useState('Normal');
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/stats`);
      setStats(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchSecurityLevel = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/security-level`);
      setSecurityLevel(res.data.level);
    } catch (err) {
      console.error(err);
    }
  };

  const refreshData = () => {
    fetchStats();
    fetchSecurityLevel();
    setRefreshKey(prev => prev + 1);
  };

  useEffect(() => {
    fetchStats();
    fetchSecurityLevel();
    const interval = setInterval(() => {
      fetchStats();
      fetchSecurityLevel();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/upload-logs`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(res.data.message);
      refreshData();
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message;
      toast.error(`Upload failed: ${errorMsg}`);
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/analyze-system`);
      toast.success(`Analyzed ${res.data.logs.length} logs, generated ${res.data.alerts.length} alerts`);
      refreshData();
    } catch (err) {
      toast.error('System analysis failed: ' + (err.response?.data?.error || err.message));
    } finally {
      setAnalyzing(false);
    }
  };

  const handleClear = async () => {
    if (!window.confirm('Are you sure you want to clear all logs and alerts? This action cannot be undone.')) {
      return;
    }
    setClearing(true);
    try {
      const res = await axios.delete(`${API_BASE_URL}/api/clear-logs`);
      toast.success(res.data.message);
      refreshData();
    } catch (err) {
      toast.error('Failed to clear logs: ' + (err.response?.data?.error || err.message));
    } finally {
      setClearing(false);
    }
  };

  const getLevelColor = () => {
    switch(securityLevel) {
      case 'Critical Emergency': return 'bg-red-700';
      case 'Under Attack': return 'bg-red-500';
      case 'Suspicious': return 'bg-yellow-500';
      case 'Elevated': return 'bg-orange-500';
      default: return 'bg-green-500';
    }
  };

  return (
    <div className="p-4">
      <div className="mb-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow flex flex-wrap justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Security Posture</h1>
          <p className="text-gray-600 dark:text-gray-400">Current Security Level</p>
        </div>
        <div className="flex flex-col items-end space-y-2">
          <div className="flex items-center space-x-4">
            <div className={`${getLevelColor()} text-white font-bold py-2 px-4 rounded-full`}>
              {securityLevel}
            </div>
            <input
              type="file"
              id="upload-logs"
              className="hidden"
              accept=".json,.log,.txt"
              onChange={handleUpload}
            />
            <label
              htmlFor="upload-logs"
              className={`bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded cursor-pointer ${uploading ? 'opacity-50' : ''}`}
            >
              {uploading ? 'Uploading...' : '📤 Upload Logs'}
            </label>
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className={`bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded ${analyzing ? 'opacity-50' : ''}`}
            >
              {analyzing ? 'Analyzing...' : '💻 Analyze My System'}
            </button>
            <button
              onClick={handleClear}
              disabled={clearing}
              className={`bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded ${clearing ? 'opacity-50' : ''}`}
            >
              {clearing ? 'Clearing...' : '🗑️ Clear Logs'}
            </button>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Supported files: <strong>.json</strong> (array of logs), <strong>.log / .txt</strong> (plain text, one log per line)
          </div>
        </div>
      </div>
      <Charts stats={stats} />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <div className="lg:col-span-2">
          <LogTable key={refreshKey} />
        </div>
        <div>
          <AlertPanel key={refreshKey} />
        </div>
      </div>
    </div>
  );
}