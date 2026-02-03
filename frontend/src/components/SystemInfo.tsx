'use client';

import { DollarSign, FileText, MessageSquare, AlertCircle, Database, Cpu } from 'lucide-react';
import { useSystemInfo, useUsage, useReadiness } from '@/hooks/useApi';

export function SystemInfo() {
  const { data: systemInfo, isLoading: infoLoading } = useSystemInfo();
  const { data: usage, isLoading: usageLoading } = useUsage();
  const { data: readiness } = useReadiness();

  if (infoLoading || usageLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-2">
        <div className="h-4 bg-gray-200 rounded w-48 animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-2">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 text-sm text-gray-600">
        {/* Left side - Usage stats */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1">
          {/* Service Status Warning */}
          {readiness && !readiness.ready && (
            <div className="flex items-center gap-1.5 text-yellow-700">
              <AlertCircle className="w-4 h-4" />
              <span>Warming up...</span>
            </div>
          )}

          {usage && (
            <>
              <div className="flex items-center gap-1.5">
                <MessageSquare className="w-4 h-4 text-gray-400" />
                <span>{usage.queries_today}/{systemInfo?.limits.max_daily_queries || 100} queries</span>
              </div>
              <div className="flex items-center gap-1.5">
                <DollarSign className="w-4 h-4 text-gray-400" />
                <span>${usage.total_cost_usd.toFixed(4)}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-gray-400" />
                <span>{usage.documents_stored}/{systemInfo?.limits.max_documents || 2} docs</span>
              </div>
            </>
          )}
        </div>

        {/* Right side - System info */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-gray-500">
          {systemInfo && (
            <>
              <div className="flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-gray-400" />
                <span>{systemInfo.pricing.llm_model}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Database className="w-4 h-4 text-gray-400" />
                <span>Qdrant</span>
              </div>
              <span className="text-xs text-gray-400">
                v{systemInfo.version}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
