export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sql?: string;
  rawData?: Record<string, unknown>[];
  suggestedChartType?: string;
  chartConfig?: ChartConfig;
  domain?: string;
  rowCount?: number;
  isError?: boolean;
}

export interface ChartConfig {
  x_key: string;
  y_keys: string[];
  title?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  backendConversationId?: string;
}

export interface ChatApiResponse {
  answer: string;
  sql: string | null;
  is_clarification: boolean;
  conversation_id: string;
  domain: string | null;
  row_count: number | null;
  raw_data: Record<string, unknown>[] | null;
  suggested_chart_type: string | null;
  chart_config: ChartConfig | null;
}

export interface ConversationGroup {
  label: string;
  conversations: Conversation[];
}
