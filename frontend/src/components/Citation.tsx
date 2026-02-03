'use client';

import { FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { Citation as CitationType } from '@/lib/api/types';

interface CitationProps {
  citation: CitationType;
  index: number;
}

export function Citation({ citation, index }: CitationProps) {
  const [expanded, setExpanded] = useState(false);

  const confidenceColor =
    citation.relevance_score >= 0.8
      ? 'bg-green-100 text-green-800'
      : citation.relevance_score >= 0.6
      ? 'bg-yellow-100 text-yellow-800'
      : 'bg-gray-100 text-gray-800';

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3 flex items-center gap-3 hover:bg-gray-50 transition-colors text-left"
      >
        <span className="flex items-center justify-center w-6 h-6 bg-primary-100 text-primary-700 rounded-full text-sm font-medium flex-shrink-0">
          {index + 1}
        </span>
        <div className="flex-grow min-w-0">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-400" />
            <span className="font-medium truncate">{citation.document_title}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500 mt-0.5">
            <span>Page {citation.page_number}</span>
            {citation.section_title && (
              <>
                <span>•</span>
                <span className="truncate">{citation.section_title}</span>
              </>
            )}
          </div>
        </div>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${confidenceColor}`}>
          {Math.round(citation.relevance_score * 100)}%
        </span>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {expanded && (
        <div className="px-3 pb-3 border-t border-gray-100">
          <div className="mt-3 p-3 bg-gray-50 rounded text-sm text-gray-700 leading-relaxed">
            <p className="italic">&ldquo;{citation.text_snippet}&rdquo;</p>
          </div>
        </div>
      )}
    </div>
  );
}

interface CitationListProps {
  citations: CitationType[];
}

export function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-gray-700 mb-2">
        Sources ({citations.length})
      </h4>
      <div className="space-y-2">
        {citations.map((citation, index) => (
          <Citation key={index} citation={citation} index={index} />
        ))}
      </div>
    </div>
  );
}
