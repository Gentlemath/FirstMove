// API functions to connect frontend with backend
const API_BASE_URL = 'http://127.0.0.1:8000';

export interface CalendarDayResponse {
  date: string;
  connected: boolean;
  source: 'google' | 'demo';
  fixed_blocks: FixedBlock[];
}

export interface WorkspaceResponse {
  date: string;
  source: 'rules' | 'llm';
  today_focus: string;
  fixed_blocks: FixedBlock[];
  task_cards: TaskCard[];
}

export interface FixedBlock {
  block_id: string;
  title: string;
  time: string;
  location?: string;
  online_link?: string;
  html_link?: string;
  note?: string;
}

export interface TaskCard {
  task_id: string;
  title: string;
  why_it_matters: string;
  first_step: string;
  hint: string;
  tools: ToolShortcut[];
  section: 'now' | 'ready' | 'later';
  status: 'now' | 'ready' | 'later' | 'finished' | 'dismissed';
}

export interface ToolShortcut {
  key: string;
  label: string;
  href: string;
  kind: 'web' | 'app';
}

export interface WorkspaceGenerateRequest {
  date?: string;
  raw_tasks: string[];
  raw_task_text?: string;
}

// Fetch today's calendar data
export async function fetchCalendarToday(date?: string): Promise<CalendarDayResponse> {
  const url = date
    ? `${API_BASE_URL}/calendar/today?target_date=${date}`
    : `${API_BASE_URL}/calendar/today`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch calendar: ${response.statusText}`);
  }
  return response.json();
}

// Fetch upcoming calendar events (future events)
export async function fetchCalendarUpcoming(daysAhead: number = 7): Promise<CalendarDayResponse> {
  const url = `${API_BASE_URL}/calendar/upcoming?days_ahead=${daysAhead}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch upcoming calendar: ${response.statusText}`);
  }
  return response.json();
}

// Generate workspace from tasks
export async function generateWorkspace(request: WorkspaceGenerateRequest): Promise<WorkspaceResponse> {
  const response = await fetch(`${API_BASE_URL}/workspace/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate workspace: ${response.statusText}`);
  }
  return response.json();
}

// Health check
export async function checkBackendHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Backend health check failed: ${response.statusText}`);
  }
  return response.json();
}
