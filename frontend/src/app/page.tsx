'use client';

import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { ChatArea } from '@/components/ChatArea';
import { useConversations } from '@/hooks/useConversations';

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const {
    conversations,
    activeConversationId,
    activeConversation,
    createNewConversation,
    setActiveConversation,
    deleteConversation,
    addMessage,
    updateLastAssistantMessage,
    setBackendConversationId,
  } = useConversations();

  // Responsive: detect mobile
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) setSidebarOpen(false);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Shift+N: New chat
      if (e.ctrlKey && e.shiftKey && e.key === 'N') {
        e.preventDefault();
        createNewConversation();
      }
      // / to focus input (when not already in an input)
      if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        e.preventDefault();
        const input = document.querySelector<HTMLTextAreaElement>('[aria-label="Chat message input"]');
        input?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [createNewConversation]);

  const handleSelectConversation = useCallback((id: string) => {
    setActiveConversation(id);
    if (isMobile) setSidebarOpen(false);
  }, [setActiveConversation, isMobile]);

  return (
    <div className="flex h-screen overflow-hidden relative">
      {/* Mobile overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <div className={isMobile ? 'fixed inset-y-0 left-0 z-30' : ''}>
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          conversations={conversations}
          activeConversationId={activeConversationId}
          onNewChat={createNewConversation}
          onSelectConversation={handleSelectConversation}
          onDeleteConversation={deleteConversation}
        />
      </div>

      {/* Main Chat Area */}
      <ChatArea
        conversation={activeConversation}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onSendMessage={addMessage}
        onUpdateAssistantMessage={updateLastAssistantMessage}
        onSetBackendConversationId={setBackendConversationId}
      />
    </div>
  );
}
