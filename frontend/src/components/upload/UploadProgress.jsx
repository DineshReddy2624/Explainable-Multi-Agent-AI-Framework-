import React from 'react';
import { Loader2, FileSpreadsheet } from 'lucide-react';

const UploadProgress = ({ progress = 75, fileName = 'dataset.csv' }) => {
  return (
    <div className="card mt-4 p-5 bg-white border border-gray-200 rounded-xl shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
          <span className="text-xs font-semibold text-gray-900 flex items-center gap-1.5">
            <FileSpreadsheet className="w-4 h-4 text-blue-600" />
            Uploading & Parsing <strong className="font-bold">{fileName}</strong>
          </span>
        </div>
        <span className="text-xs font-bold text-blue-600">{progress}%</span>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-600 transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

export default UploadProgress;
