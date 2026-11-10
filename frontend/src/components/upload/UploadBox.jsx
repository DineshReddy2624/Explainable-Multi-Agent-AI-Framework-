import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, FileText, CheckCircle2 } from 'lucide-react';

const UploadBox = ({ onFileUpload }) => {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files[0]);
    }
  };

  const handleButtonClick = (e) => {
    e.stopPropagation();
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          onFileUpload(e.dataTransfer.files[0]);
        }
      }}
      onClick={() => fileInputRef.current?.click()}
      className={`card flex flex-col items-center justify-center p-10 border-2 border-dashed cursor-pointer transition-all text-center ${
        dragOver ? 'border-blue-500 bg-blue-50/50' : 'border-gray-300 hover:border-gray-400 bg-white'
      }`}
    >
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        onChange={handleFileChange}
        accept=".csv,.xlsx,.xls,.parquet,.pdf"
      />
      <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-sm">
        <UploadCloud className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-gray-900 mb-1">Drag & Drop your dataset or PDF file here</h3>
      <p className="text-xs text-gray-500 max-w-sm mb-4">
        Supports CSV, XLSX, Parquet, and PDF files up to 100MB for real-time profiling, multi-agent analysis, and before/after report generation.
      </p>

      <div className="flex items-center gap-2 mb-6 text-xs text-gray-400">
        <span className="flex items-center gap-1 font-medium bg-gray-100 px-2.5 py-1 rounded-md text-gray-600">
          <FileSpreadsheet className="w-3.5 h-3.5 text-blue-600" /> .CSV
        </span>
        <span className="flex items-center gap-1 font-medium bg-gray-100 px-2.5 py-1 rounded-md text-gray-600">
          <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" /> .XLSX
        </span>
        <span className="flex items-center gap-1 font-medium bg-gray-100 px-2.5 py-1 rounded-md text-gray-600">
          <FileSpreadsheet className="w-3.5 h-3.5 text-indigo-600" /> .PARQUET
        </span>
        <span className="flex items-center gap-1 font-medium bg-gray-100 px-2.5 py-1 rounded-md text-gray-600">
          <FileText className="w-3.5 h-3.5 text-red-600" /> .PDF
        </span>
      </div>


      <button
        type="button"
        className="btn btn-primary btn-sm flex items-center gap-2 font-semibold"
        onClick={handleButtonClick}
      >
        <span>Browse Local Files</span>
      </button>
    </div>
  );
};

export default UploadBox;
