'use client';

import { MessageSquarePlus, PanelLeftClose, Trash2 } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { Conversation } from '@/types';
import { clsx } from 'clsx';
import { groupConversationsByDate } from '@/lib/utils';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
}

export function Sidebar({
  isOpen,
  onToggle,
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
}: SidebarProps) {
  const grouped = groupConversationsByDate(conversations);

  if (!isOpen) return null;

  return (
    <aside className="w-64 h-full flex flex-col bg-sidebar dark:bg-sidebar-dark border-r border-border-light dark:border-border-dark animate-slide-in">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-border-light dark:border-border-dark">
        <button
          onClick={onNewChat}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex-1"
          aria-label="New chat"
        >
          <MessageSquarePlus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
        <button
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          aria-label="Close sidebar"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* Conversation List */}
      <nav className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-4">
        {grouped.map((group) => (
          <div key={group.label}>
            <h3 className="px-2 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {group.label}
            </h3>
            <ul className="space-y-0.5">
              {group.conversations.map((conv) => (
                <li key={conv.id} className="group relative">
                  <button
                    onClick={() => onSelectConversation(conv.id)}
                    className={clsx(
                      'w-full text-left px-3 py-2 text-sm rounded-lg truncate transition-colors',
                      conv.id === activeConversationId
                        ? 'bg-gray-200 dark:bg-gray-700 font-medium'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                    )}
                    title={conv.title}
                  >
                    {conv.title || 'New conversation'}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-300 dark:hover:bg-gray-600 transition-all"
                    aria-label={`Delete conversation: ${conv.title}`}
                  >
                    <Trash2 className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}

        {conversations.length === 0 && (
          <p className="px-3 py-8 text-sm text-gray-400 dark:text-gray-500 text-center">
            No conversations yet. Start a new chat!
          </p>
        )}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-border-light dark:border-border-dark flex items-center justify-between">
        <span className="text-xs text-gray-400 dark:text-gray-500">College Chatbot</span>
        <ThemeToggle />
      </div>
    </aside>
  );
}
