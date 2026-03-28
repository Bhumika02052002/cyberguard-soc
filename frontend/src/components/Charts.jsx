import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function Charts({ stats }) {
  const { failed_logins, successful_logins, alerts_per_type, hourly_traffic } = stats;

  // Data for failed vs successful logins
  const loginData = [
    { name: 'Failed', value: failed_logins },
    { name: 'Successful', value: successful_logins }
  ];

  // Data for alerts per type
  const alertTypeData = Object.keys(alerts_per_type).map(key => ({
    name: key,
    value: alerts_per_type[key]
  }));

  // Data for traffic over time
  const trafficData = hourly_traffic.map((count, index) => ({
    hour: index,
    requests: count
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4">
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Login Attempts</h3>
        <PieChart width={300} height={300}>
          <Pie
            data={loginData}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {loginData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Alerts by Type</h3>
        <BarChart width={400} height={300} data={alertTypeData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="value" fill="#8884d8" />
        </BarChart>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow col-span-full">
        <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Traffic over Last 24 Hours</h3>
        <LineChart width={800} height={300} data={trafficData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="hour" label={{ value: 'Hour (0-23)', position: 'insideBottom', offset: -5 }} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="requests" stroke="#8884d8" />
        </LineChart>
      </div>
    </div>
  );
}