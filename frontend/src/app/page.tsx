'use client';

import { Scale, LogOut, Loader2 } from 'lucide-react';
import { DocumentUpload } from '@/components/DocumentUpload';
import { DocumentList } from '@/components/DocumentList';
import { ChatInterface } from '@/components/ChatInterface';
import { SystemInfo } from '@/components/SystemInfo';
import { Login } from '@/components/Login';
import { useAuth } from '@/contexts/AuthContext';
import { useDocuments } from '@/hooks/useApi';

export default function Home() {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const { data: documents } = useDocuments();
  const hasDocuments = (documents?.total || 0) > 0;

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <main className="h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Scale className="w-8 h-8 text-primary-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">Legal AI Assistant</h1>
              <p className="text-sm text-gray-500">
                Upload legal documents and ask questions with source citations
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-700 text-sm"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden max-w-7xl mx-auto px-4 py-4 w-full flex flex-col">
        {/* POC Disclaimer */}
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex-shrink-0">
          <h2 className="font-semibold text-blue-900 mb-1">
            Proof of Concept Demo
          </h2>
          <p className="text-sm text-blue-800">
            This is a demonstration system. Answers are generated using AI and should be verified
            against source documents. This is not legal advice. OpenAI GPT-4o is used for answer
            generation with associated costs.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
          {/* Left Column - Documents */}
          <div className="space-y-4 overflow-y-auto">
            <DocumentUpload
              disabled={documents?.limit_reached}
            />
            <DocumentList />
          </div>

          {/* Right Columns - Chat (wider) */}
          <div className="lg:col-span-2 min-h-0 flex flex-col">
            <ChatInterface hasDocuments={hasDocuments} />
          </div>
        </div>
      </div>

      {/* System Info Bar */}
      <div className="border-t border-gray-200 bg-gray-50 flex-shrink-0">
        <SystemInfo />
      </div>
    </main>
  );
}
