// Frontend types - should match backend API types
import { TaskCard } from "./api";
export type FixedBlock = {
  id: string;
  title: string;
  time: string;
  location?: string;
  online_link?: string;
  html_link?: string;
};

export type CalendarDayResponse = {
  date: string;
  connected: boolean;
  source: "google" | "demo";
  fixed_blocks: FixedBlock[];
};

export type WorkspaceResponse = {
  date: string;
  source: "rules" | "llm";
  today_focus: string;
  fixed_blocks: FixedBlock[];
  task_cards: TaskCard[];
};

export type WorkspaceGenerateRequest = {
  date?: string;
  raw_tasks: string[];
  raw_task_text?: string;
};
