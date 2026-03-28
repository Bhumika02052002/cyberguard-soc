import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { API_BASE_URL } from '../config';

export default function Reports() {
  const [loading, setLoading] = useState(false);

  const downloadPDF = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/report/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'cyberguard_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Report downloaded');
    } catch (err) {
      toast.error('Failed to generate report');
    }
    setLoading(false);
  };

  const uploadLogs = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API_BASE_URL}/upload-logs`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(res.data.message);
    } catch (err) {
      toast.error('Upload failed: ' + (err.response?.data?.error || err.message));
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6 text-gray-800 dark:text-white">Reports & Data Management</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 max-w-md">
        <h2 className="text-xl font-semibold mb-4">Generate PDF Report</h2>
        <button
          onClick={downloadPDF}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded mb-6"
        >
          {loading ? 'Generating...' : 'Download PDF Report'}
        </button>

        <h2 className="text-xl font-semibold mb-4">Upload Logs (JSON, .log, .txt)</h2>
        <input
          type="file"
          accept=".json,.log,.txt"
          onChange={uploadLogs}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
      </div>
    </div>
  );
}