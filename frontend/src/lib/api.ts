import { ChatApiResponse, Conversation, Message } from '@/types';

function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;
  if (!envUrl) {
    return 'http://localhost:8000/api';
  }

  let cleanUrl = envUrl.trim().replace(/\/+$/, '');
  if (cleanUrl.endsWith('/api')) {
    cleanUrl = cleanUrl.slice(0, -4);
  }
  if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
    cleanUrl = `https://${cleanUrl}`;
  }
  return `${cleanUrl}/api`;
}

export async function sendChatMessage(
  question: string,
  conversationId?: string
): Promise<ChatApiResponse> {
  const apiBase = getApiBaseUrl();
  const body: Record<string, string> = { question };
  if (conversationId) {
    body.conversation_id = conversationId;
  }

  const response = await fetch(`${apiBase}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).catch((err) => {
    throw new Error(`Cannot connect to Backend Server (${err.message || 'Network error'}). Please verify your Render backend status and NEXT_PUBLIC_BACKEND_URL.`);
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Conversation persistence API

export async function fetchConversations(page = 1, pageSize = 50) {
  try {
    const apiBase = getApiBaseUrl();
    const response = await fetch(`${apiBase}/conversations?page=${page}&page_size=${pageSize}`);
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function fetchConversation(id: string) {
  try {
    const apiBase = getApiBaseUrl();
    const response = await fetch(`${apiBase}/conversations/${id}`);
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function saveConversation(conversation: Conversation) {
  try {
    const apiBase = getApiBaseUrl();
    const body = {
      id: conversation.id,
      title: conversation.title,
      created_at: conversation.createdAt,
      updated_at: conversation.updatedAt,
      messages: conversation.messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        sql_query: msg.sql || null,
        raw_data: msg.rawData || null,
        chart_type: msg.suggestedChartType || null,
        chart_config: msg.chartConfig || null,
        domain: msg.domain || null,
        row_count: msg.rowCount || null,
        created_at: msg.timestamp,
      })),
    };

    const response = await fetch(`${apiBase}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    return response.ok;
  } catch {
    return false;
  }
}

export async function deleteConversationApi(id: string) {
  try {
    const apiBase = getApiBaseUrl();
    const response = await fetch(`${apiBase}/delete_conversation/${id}`, {
      method: 'DELETE',
    });
    return response.ok || response.status === 204;
  } catch {
    return false;
  }
}
