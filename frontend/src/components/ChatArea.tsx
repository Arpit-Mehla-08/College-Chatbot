'use client';

import { useRef, useEffect, useState } from 'react';
import { PanelLeft } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { ExampleChips } from './ExampleChips';
import { Conversation, Message } from '@/types';
import { sendChatMessage } from '@/lib/api';

interface ChatAreaProps {
  conversation: Conversation | null;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  onSendMessage: (message: Message) => void;
  onUpdateAssistantMessage: (message: Message) => void;
  onSetBackendConversationId: (conversationId: string, backendId: string) => void;
}

export function ChatArea({
  conversation,
  sidebarOpen,
  onToggleSidebar,
  onSendMessage,
  onUpdateAssistantMessage,
  onSetBackendConversationId,
}: ChatAreaProps) {
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const messages = conversation?.messages || [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };
    onSendMessage(userMessage);

    setIsLoading(true);

    try {
      // Capture conversation ID before async call (may change during await)
      const currentConvId = conversation?.id;
      const backendConvId = conversation?.backendConversationId;

      const response = await sendChatMessage(
        content.trim(),
        backendConvId || undefined
      );

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        sql: response.sql || undefined,
        rawData: response.raw_data || undefined,
        suggestedChartType: response.suggested_chart_type || undefined,
        chartConfig: response.chart_config || undefined,
        domain: response.domain || undefined,
        rowCount: response.row_count || undefined,
        isError: false,
      };

      onUpdateAssistantMessage(assistantMessage);

      // Store backend conversation ID properly through state
      if (response.conversation_id) {
        // Use currentConvId if available, otherwise find the active conversation
        const convId = currentConvId;
        if (convId) {
          onSetBackendConversationId(convId, response.conversation_id);
        }
      }
    } catch (error: any) {
      const errorMessageText = error?.message && error.message !== 'Failed to fetch'
        ? `Error: ${error.message}`
        : 'Could not connect to the backend server. Please check if your Render backend is running, or wait a few seconds if Render is waking up from idle (cold start).';

      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: errorMessageText,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      onUpdateAssistantMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <main className="flex-1 flex flex-col h-full min-w-0">
      {/* Header */}
      <header className="flex items-center gap-2 px-4 py-3 border-b border-border-light dark:border-border-dark">
        {!sidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            aria-label="Open sidebar"
          >
            <PanelLeft className="w-5 h-5" />
          </button>
        )}
        <h1 className="text-sm font-medium text-gray-600 dark:text-gray-300">
          College Data Assistant
        </h1>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full px-4">
            <div className="max-w-md text-center space-y-4">
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">
                College Data Assistant
              </h2>
              <p className="text-gray-500 dark:text-gray-400">
                Ask questions about students, attendance, results, and more. I'll translate your questions into data insights.
              </p>
              <ExampleChips onSelect={handleSendMessage} />
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-border-light dark:border-border-dark px-4 py-3">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
    </main>
  );
}
