'use client';

import { FileText, Trash2, Loader2, AlertCircle } from 'lucide-react';
import { useDocuments, useDeleteDocument, getErrorMessage } from '@/hooks/useApi';
import type { DocumentSummary } from '@/lib/api/types';

interface DocumentListProps {
  onDocumentSelect?: (doc: DocumentSummary) => void;
  selectedDocumentId?: string;
}

export function DocumentList({ onDocumentSelect, selectedDocumentId }: DocumentListProps) {
  const { data, isLoading, isError, error } = useDocuments();
  const deleteMutation = useDeleteDocument();

  const handleDelete = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this document?')) {
      await deleteMutation.mutateAsync(docId);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Documents</h2>
        <div className="flex items-center justify-center py-8 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Loading documents...
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Documents</h2>
        <div className="flex items-center gap-2 text-red-600 py-4">
          <AlertCircle className="w-5 h-5" />
          <span>{getErrorMessage(error)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Documents</h2>
        <span className="text-sm text-gray-500">
          {data?.total || 0} / 10 documents
        </span>
      </div>

      {data?.limit_reached && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
          Document limit reached. Delete a document to upload more.
        </div>
      )}

      {data?.documents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No documents uploaded yet.</p>
          <p className="text-sm">Upload a PDF to get started.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {data?.documents.map((doc) => (
            <div
              key={doc.id}
              onClick={() => onDocumentSelect?.(doc)}
              className={`
                p-3 rounded-lg border cursor-pointer transition-colors
                ${
                  selectedDocumentId === doc.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
                <div className="flex-grow min-w-0">
                  <h3 className="font-medium truncate">{doc.title}</h3>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500 mt-1">
                    <span>{doc.page_count} pages</span>
                    <span>{doc.chunk_count} chunks</span>
                    <span>{formatDate(doc.uploaded_at)}</span>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDelete(e, doc.id)}
                  disabled={deleteMutation.isPending}
                  className="p-1.5 hover:bg-red-100 rounded text-gray-400 hover:text-red-600 transition-colors"
                  title="Delete document"
                >
                  {deleteMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {deleteMutation.isError && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {getErrorMessage(deleteMutation.error)}
        </div>
      )}
    </div>
  );
}
