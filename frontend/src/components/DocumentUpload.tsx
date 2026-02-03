'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, FileText, X, Loader2 } from 'lucide-react';
import { useUploadDocument, getErrorMessage } from '@/hooks/useApi';

interface DocumentUploadProps {
  onSuccess?: () => void;
  disabled?: boolean;
}

export function DocumentUpload({ onSuccess, disabled }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useUploadDocument();

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
      }
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    try {
      await uploadMutation.mutateAsync({
        file,
        title: title || undefined,
      });
      setFile(null);
      setTitle('');
      onSuccess?.();
    } catch (error) {
      // Error is handled by the mutation
    }
  }, [file, title, uploadMutation, onSuccess]);

  const clearFile = useCallback(() => {
    setFile(null);
    setTitle('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4">Upload Document</h2>

      {/* Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${dragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
        />
        <Upload className="w-10 h-10 mx-auto mb-3 text-gray-400" />
        <p className="text-gray-600 mb-1">
          Drag and drop a PDF file here, or click to select
        </p>
        <p className="text-sm text-gray-400">
          Max 10MB, 80 pages per document
        </p>
      </div>

      {/* Selected File */}
      {file && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg flex items-center gap-3">
          <FileText className="w-8 h-8 text-primary-600 flex-shrink-0" />
          <div className="flex-grow min-w-0">
            <p className="font-medium truncate">{file.name}</p>
            <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              clearFile();
            }}
            className="p-1 hover:bg-gray-200 rounded"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      )}

      {/* Title Input */}
      {file && (
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Document Title (optional)
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter a custom title"
            className="input"
            disabled={uploadMutation.isPending}
          />
        </div>
      )}

      {/* Error Message */}
      {uploadMutation.isError && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {getErrorMessage(uploadMutation.error)}
        </div>
      )}

      {/* Success Message */}
      {uploadMutation.isSuccess && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          Document uploaded successfully! {uploadMutation.data.chunk_count} chunks created.
        </div>
      )}

      {/* Upload Button */}
      {file && (
        <button
          onClick={handleUpload}
          disabled={uploadMutation.isPending || disabled}
          className="mt-4 btn btn-primary w-full flex items-center justify-center gap-2"
        >
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Upload Document
            </>
          )}
        </button>
      )}
    </div>
  );
}
