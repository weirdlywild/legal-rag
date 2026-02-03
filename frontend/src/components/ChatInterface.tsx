'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { Send, Loader2, AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useQueryDocuments, getErrorMessage } from '@/hooks/useApi';
import { CitationList } from './Citation';
import type { QueryResponse, Citation as CitationType } from '@/lib/api/types';

interface ChatMessage {
  type: 'user' | 'assistant' | 'error';
  content: string;
  citations?: CitationType[];
  confidence?: 'high' | 'medium' | 'low';
  usage?: QueryResponse['usage'];
  warning?: string;
}

interface ChatInterfaceProps {
  hasDocuments: boolean;
}

export function ChatInterface({ hasDocuments }: ChatInterfaceProps) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const queryMutation = useQueryDocuments();

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!question.trim() || queryMutation.isPending) return;

      const userQuestion = question.trim();
      setQuestion('');

      // Add user message
      setMessages((prev) => [...prev, { type: 'user', content: userQuestion }]);

      try {
        const response = await queryMutation.mutateAsync({
          question: userQuestion,
        });

        // Add assistant message
        setMessages((prev) => [
          ...prev,
          {
            type: 'assistant',
            content: response.answer,
            citations: response.citations,
            confidence: response.confidence,
            usage: response.usage,
            warning: response.warning,
          },
        ]);
      } catch (error: any) {
        // Check for insufficient evidence response
        const errorData = error.response?.data?.detail;
        if (errorData && typeof errorData === 'object' && 'message' in errorData) {
          setMessages((prev) => [
            ...prev,
            {
              type: 'error',
              content: errorData.message,
              citations: errorData.partial_context || [],
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              type: 'error',
              content: getErrorMessage(error),
            },
          ]);
        }
      }
    },
    [question, queryMutation]
  );

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'medium':
        return <HelpCircle className="w-4 h-4 text-yellow-500" />;
      case 'low':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      default:
        return null;
    }
  };

  const getConfidenceLabel = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'High confidence';
      case 'medium':
        return 'Medium confidence';
      case 'low':
        return 'Low confidence';
      default:
        return '';
    }
  };

  return (
    <div className="card flex flex-col h-full">
      <h2 className="text-lg font-semibold mb-4">Ask Questions</h2>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <HelpCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Ask a question about your documents.</p>
            <p className="text-sm mt-1">
              Questions should be at least 10 characters long.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-lg p-4 ${
                  msg.type === 'user'
                    ? 'bg-primary-600 text-white'
                    : msg.type === 'error'
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-gray-100'
                }`}
              >
                {msg.type === 'error' && (
                  <div className="flex items-center gap-2 text-red-600 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="font-medium">Could not answer</span>
                  </div>
                )}

                {msg.type === 'assistant' ? (
                  <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-li:text-gray-700 prose-strong:text-gray-900">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <div className={`whitespace-pre-wrap ${msg.type === 'error' ? 'text-red-700' : ''}`}>
                    {msg.content}
                  </div>
                )}

                {/* Confidence indicator */}
                {msg.confidence && (
                  <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-gray-200">
                    {getConfidenceIcon(msg.confidence)}
                    <span className="text-sm text-gray-600">
                      {getConfidenceLabel(msg.confidence)}
                    </span>
                  </div>
                )}

                {/* Warning */}
                {msg.warning && (
                  <div className="mt-3 p-2 bg-yellow-50 rounded text-sm text-yellow-800 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    {msg.warning}
                  </div>
                )}

                {/* Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <CitationList citations={msg.citations} />
                )}

                {/* Usage stats */}
                {msg.usage && (
                  <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500 space-y-1">
                    <div className="flex flex-wrap gap-x-3 gap-y-1">
                      <span>Cost: ${msg.usage.estimated_cost_usd.toFixed(4)}</span>
                      <span>Tokens: {msg.usage.llm_input_tokens + msg.usage.llm_output_tokens}</span>
                    </div>
                    {msg.usage.timing && (
                      <div className="flex flex-wrap gap-x-3 gap-y-1 text-gray-400">
                        <span>Embed: {(msg.usage.timing.embedding_ms / 1000).toFixed(2)}s</span>
                        <span>Search: {(msg.usage.timing.search_ms / 1000).toFixed(2)}s</span>
                        <span>LLM: {(msg.usage.timing.llm_ms / 1000).toFixed(2)}s</span>
                        <span className="text-gray-500 font-medium">Total: {(msg.usage.timing.total_ms / 1000).toFixed(2)}s</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={
            hasDocuments
              ? 'Ask a question about your documents...'
              : 'Upload a document first to ask questions'
          }
          className="input flex-1"
          disabled={!hasDocuments || queryMutation.isPending}
          maxLength={500}
        />
        <button
          type="submit"
          disabled={!hasDocuments || !question.trim() || question.length < 10 || queryMutation.isPending}
          className="btn btn-primary flex items-center gap-2"
        >
          {queryMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          Ask
        </button>
      </form>

      {question.length > 0 && question.length < 10 && (
        <p className="text-sm text-gray-500 mt-1">
          {10 - question.length} more characters needed
        </p>
      )}
    </div>
  );
}
