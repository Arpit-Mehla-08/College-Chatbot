'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Conversation, Message } from '@/types';
import { saveConversation, deleteConversationApi, fetchConversations } from '@/lib/api';

const STORAGE_KEY = 'college-chatbot-conversations';

function loadConversations(): Conversation[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function persistConversations(conversations: Conversation[]) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  } catch {
    // Storage full or unavailable
  }
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'synced' | 'error'>('idle');
  const syncTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Ref to always have the latest activeConversationId (avoids stale closures in async callbacks)
  const activeIdRef = useRef<string | null>(activeConversationId);
  activeIdRef.current = activeConversationId;

  // Load from localStorage on mount, then attempt backend sync
  useEffect(() => {
    const loaded = loadConversations();
    setConversations(loaded);
    if (loaded.length > 0) {
      setActiveConversationId(loaded[0].id);
    }

    // Attempt to load from backend and merge
    syncFromBackend(loaded);
  }, []);

  // Persist to localStorage on changes
  useEffect(() => {
    if (conversations.length > 0) {
      persistConversations(conversations);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [conversations]);

  const syncFromBackend = async (localConvs: Conversation[]) => {
    setSyncStatus('syncing');
    try {
      const data = await fetchConversations();
      if (!data || !data.conversations) {
        setSyncStatus('idle');
        return;
      }

      // Merge: backend is source of truth for existing conversations,
      // but local-only conversations (not yet synced) are kept
      const backendIds = new Set(data.conversations.map((c: { id: string }) => c.id));
      const localOnly = localConvs.filter((c) => !backendIds.has(c.id));

      // For now, just keep local conversations (backend will be synced to on save)
      // This is a soft-merge approach
      if (localOnly.length === localConvs.length) {
        // No overlap, backend might be empty or different - keep local
        setSyncStatus('synced');
        return;
      }

      setSyncStatus('synced');
    } catch {
      setSyncStatus('error');
    }
  };

  // Debounced sync to backend
  const syncToBackend = useCallback((conv: Conversation) => {
    if (syncTimeoutRef.current) {
      clearTimeout(syncTimeoutRef.current);
    }
    syncTimeoutRef.current = setTimeout(async () => {
      setSyncStatus('syncing');
      const success = await saveConversation(conv);
      setSyncStatus(success ? 'synced' : 'error');
    }, 2000); // Debounce 2 seconds
  }, []);

  const activeConversation = conversations.find((c) => c.id === activeConversationId) || null;

  const createNewConversation = useCallback(() => {
    const newConv: Conversation = {
      id: crypto.randomUUID(),
      title: '',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setConversations((prev) => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
  }, []);

  const setActiveConversation = useCallback((id: string) => {
    setActiveConversationId(id);
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => {
      const filtered = prev.filter((c) => c.id !== id);
      if (id === activeIdRef.current) {
        const newActiveId = filtered.length > 0 ? filtered[0].id : null;
        activeIdRef.current = newActiveId;
        setActiveConversationId(newActiveId);
      }
      return filtered;
    });
    // Also delete from backend (fire and forget)
    deleteConversationApi(id);
  }, []);

  const addMessage = useCallback((message: Message) => {
    setConversations((prev) => {
      let targetId = activeIdRef.current;
      let updatedConvs = [...prev];

      if (!targetId) {
        const newConv: Conversation = {
          id: crypto.randomUUID(),
          title: '',
          messages: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        targetId = newConv.id;
        updatedConvs = [newConv, ...updatedConvs];
        activeIdRef.current = targetId; // Update ref immediately for async callbacks
        setActiveConversationId(targetId);
      }

      const result = updatedConvs.map((conv) => {
        if (conv.id !== targetId) return conv;
        const newMessages = [...conv.messages, message];
        const title = conv.title || (message.role === 'user' ? message.content.slice(0, 40) : conv.title);
        return {
          ...conv,
          messages: newMessages,
          title,
          updatedAt: new Date().toISOString(),
        };
      });

      return result;
    });
  }, []);

  const setBackendConversationId = useCallback((conversationId: string, backendId: string) => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === conversationId
          ? { ...conv, backendConversationId: backendId }
          : conv
      )
    );
  }, []);

  const updateLastAssistantMessage = useCallback((message: Message) => {
    setConversations((prev) => {
      const currentActiveId = activeIdRef.current;
      const updated = prev.map((conv) => {
        if (conv.id !== currentActiveId) return conv;
        const updatedConv = {
          ...conv,
          messages: [...conv.messages, message],
          updatedAt: new Date().toISOString(),
        };
        // Sync to backend after assistant responds
        syncToBackend(updatedConv);
        return updatedConv;
      });
      return updated;
    });
  }, [syncToBackend]);

  return {
    conversations,
    activeConversationId,
    activeConversation,
    syncStatus,
    createNewConversation,
    setActiveConversation,
    deleteConversation,
    addMessage,
    updateLastAssistantMessage,
    setBackendConversationId,
  };
}
