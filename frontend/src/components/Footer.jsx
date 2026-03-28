import React from 'react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white dark:bg-gray-800 shadow-inner mt-8">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center text-sm text-gray-600 dark:text-gray-400">
          <div className="mb-2 md:mb-0">
            <span className="font-semibold">CyberGuard SOC</span> – Real-time threat monitoring & alerting
          </div>
          <div className="flex space-x-4">
            <span>© {currentYear}</span>
            <span>Developed by Bhumika Mishra</span>
          </div>
        </div>
      </div>
    </footer>
  );
}