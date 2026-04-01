"use client";

import { useState, useEffect } from "react";

import AppHeader from "./AppHeader";
import FixedBlocks from "./FixedBlocks";
import GreetingPanel from "./GreetingPanel";
import TaskInputBox from "./TaskInputBox";
import WorkspaceColumn from "./WorkspaceColumn";
import { fetchCalendarToday, fetchCalendarUpcoming, generateWorkspace, CalendarDayResponse, WorkspaceResponse, TaskCard } from "../lib/api";
import { FixedBlock } from "../lib/types";

const defaultTaskInput = `Reply to recruiter
Finish product spec
Prepare for project review`;

export default function FirstMoveDashboard() {
  const [taskInput, setTaskInput] = useState(defaultTaskInput);
  const [workspaceGenerated, setWorkspaceGenerated] = useState(false);

  // API state
  const [calendarData, setCalendarData] = useState<CalendarDayResponse | null>(null);
  const [workspaceData, setWorkspaceData] = useState<WorkspaceResponse | null>(null);
  const [taskStatusMap, setTaskStatusMap] = useState<Record<string, TaskCard["status"]>>({});
  const [selectedWorkspaceTaskId, setSelectedWorkspaceTaskId] = useState<string | null>(null);
  const [isLoadingCalendar, setIsLoadingCalendar] = useState(true);
  const [isGeneratingWorkspace, setIsGeneratingWorkspace] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper function to fetch calendar data (today's events)
  const loadCalendarData = async () => {
    try {
      setIsLoadingCalendar(true);
      const data = await fetchCalendarToday();
      setCalendarData(data);
    } catch (err) {
      console.error('Failed to load calendar data:', err);
      setError(`Failed to load calendar data: ${err instanceof Error ? err.message : 'Unknown error'}. Using demo data.`);
      // Fallback to demo data if API fails
      setCalendarData({
        date: new Date().toISOString().split('T')[0],
        connected: false,
        source: 'demo',
        fixed_blocks: [
          {
            block_id: "block-1",
            title: "Team Sync",
            time: "10:00–10:30",
            location: "Google Meet",
            note: "notes ready",
          },
          {
            block_id: "block-2",
            title: "Project Review",
            time: "3:00–4:00",
            location: "Zoom",
            note: "deck linked",
          },
        ]
      });
    } finally {
      setIsLoadingCalendar(false);
    }
  };

  // Fetch calendar data on component mount
  useEffect(() => {
    loadCalendarData();
  }, []);

  // Helper to reorder active tasks with proper status distribution
  const reorderTaskStatuses = (tasks: TaskCard[], currentStatusMap: Record<string, TaskCard["status"]>) => {
    // Filter out finished/dismissed tasks to find active tasks
    const activeTasks = tasks.filter(task => {
      const effectiveStatus = currentStatusMap[task.task_id] || task.status;
      return effectiveStatus !== "finished" && effectiveStatus !== "dismissed";
    });

    // Build new status map with re-indexed active tasks
    const newMap: Record<string, TaskCard["status"]> = {};
    
    activeTasks.forEach((task, index) => {
      if (index === 0) {
        newMap[task.task_id] = "now";
      } else if (index === 1 || index === 2) {
        newMap[task.task_id] = "ready";
      } else {
        newMap[task.task_id] = "later";
      }
    });

    // Preserve finished/dismissed statuses
    tasks.forEach(task => {
      const effectiveStatus = currentStatusMap[task.task_id] || task.status;
      if (effectiveStatus === "finished" || effectiveStatus === "dismissed") {
        newMap[task.task_id] = effectiveStatus;
      }
    });

    return newMap;
  };

  // Handle workspace generation
  const handleGenerateWorkspace = async () => {
    try {
      setIsGeneratingWorkspace(true);
      setError(null);

      // Always refresh calendar data
      await loadCalendarData();

      // Check if there are tasks to process
      const trimmedInput = taskInput.trim();
      if (!trimmedInput) {
        // No tasks - just refresh calendar and return
        return;
      }

      // Process new tasks through LLM
      const rawTasks = trimmedInput
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

      const request = {
        raw_tasks: rawTasks,
        raw_task_text: taskInput,
      };

      const data = await generateWorkspace(request);
      
      // Merge old and new tasks instead of replacing
      if (workspaceData) {
        const existingTasks = workspaceData.task_cards || [];
        // Re-index new tasks with unique IDs to avoid duplicates
        const reindexedNewTasks = data.task_cards.map((task, index) => ({
          ...task,
          task_id: `task-${existingTasks.length + index + 1}`,
        }));
        const mergedTasks = [...existingTasks, ...reindexedNewTasks];
        setWorkspaceData({
          ...data,
          task_cards: mergedTasks,
        });
        // Reorder all tasks after merging new ones
        setTaskStatusMap(reorderTaskStatuses(mergedTasks, taskStatusMap));
      } else {
        setWorkspaceData(data);
        // Reorder tasks for initial generation
        setTaskStatusMap(reorderTaskStatuses(data.task_cards, {}));
      }
      
      setWorkspaceGenerated(true);
      setSelectedWorkspaceTaskId(data.task_cards?.[0]?.task_id ?? null);
      // Clear processed input so new tasks can be entered
      setTaskInput("");
    } catch (err) {
      console.error('Failed to generate workspace:', err);
      setError('Failed to generate workspace. Please try again.');
    } finally {
      setIsGeneratingWorkspace(false);
    }
  };

  // Handle task status change
  const handleTaskStatusChange = (taskId: string, newStatus: TaskCard["status"]) => {
    setTaskStatusMap(prev => {
      // Create updated map with new status
      const updated = {
        ...prev,
        [taskId]: newStatus,
      };
      // Reorder all active tasks
      return reorderTaskStatuses(workspaceTasks, updated);
    });
  };

  // Get fixed blocks from calendar data or fallback
  const fixedBlocks = calendarData?.fixed_blocks || [];
  const workspaceTasks = workspaceData?.task_cards || [];

  // Convert backend FixedBlock format to frontend format
  const frontendFixedBlocks: FixedBlock[] = fixedBlocks.map(block => ({
    id: block.block_id,
    title: block.title,
    time: block.time,
    location: block.online_link ? `Online` : block.location,
    online_link: block.online_link ?? undefined,
    html_link: block.html_link ?? undefined,
  }));

  const selectedTask = workspaceTasks.find((task) => task.task_id === selectedWorkspaceTaskId) || workspaceTasks[0] || null;
  
  // Apply status overrides from taskStatusMap
  const selectedTaskWithStatus = selectedTask ? {
    ...selectedTask,
    status: taskStatusMap[selectedTask.task_id] || selectedTask.status,
  } : null;

  return (
    <div className="min-h-screen bg-slate-100 lg:h-dvh lg:overflow-hidden">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-3 p-4 md:p-6 lg:h-dvh lg:min-h-0 lg:max-w-[1440px] lg:overflow-hidden lg:px-5 lg:py-4">
        <AppHeader />

        {/* Error display */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
            {error}
          </div>
        )}

        {!workspaceGenerated ? (
          <section className="grid gap-3 lg:flex-1 lg:min-h-0 lg:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
            <GreetingPanel
              blocks={frontendFixedBlocks}
              isLoading={isLoadingCalendar}
            />
            <TaskInputBox
              value={taskInput}
              onChange={setTaskInput}
              onGenerate={handleGenerateWorkspace}
              isGenerating={isGeneratingWorkspace}
            />
          </section>
        ) : (
          <section className="grid gap-3 lg:flex-1 lg:min-h-0 lg:h-full lg:grid-cols-[320px_minmax(0,1fr)] lg:overflow-hidden">
            <div className="flex flex-col gap-3 lg:min-h-0 lg:h-full lg:overflow-hidden">
              <section className="rounded-3xl border border-slate-200 bg-white/80 shadow-sm lg:flex-1 lg:min-h-0 lg:overflow-hidden">
                <div className="border-b border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">
                  Today&apos;s fixed blocks
                </div>
                <div className="p-3 lg:h-full lg:overflow-auto">
                  <FixedBlocks blocks={frontendFixedBlocks} stacked compact />
                </div>
              </section>

              <div className="mt-auto">
                <TaskInputBox
                  value={taskInput}
                  onChange={setTaskInput}
                  onGenerate={handleGenerateWorkspace}
                  generated
                  compact
                />
              </div>
            </div>

            {workspaceData ? (
              <div className="flex flex-col gap-3 lg:min-h-0 lg:h-full lg:overflow-hidden">
                <WorkspaceColumn
                  title="Your daily workspace"
                  tasks={workspaceData.task_cards}
                  selectedTaskId={selectedWorkspaceTaskId}
                  onSelectTask={setSelectedWorkspaceTaskId}
                  onStatusChange={handleTaskStatusChange}
                  taskStatusMap={taskStatusMap}
                  showDetail={true}
                />
              </div>             
            ) : (
              <div className="flex items-center justify-center p-8 text-slate-500">
                No workspace data available
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
