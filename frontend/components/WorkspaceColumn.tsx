import { useState } from "react";

import TaskCard from "./TaskCard";
import { TaskCard as TaskCardType } from "../lib/api";

type WorkspaceColumnProps = {
  title: string;
  tasks: TaskCardType[];
  selectedTaskId?: string | null;
  onSelectTask?: (taskId: string) => void;
  onStatusChange?: (taskId: string, status: TaskCardType["status"]) => void;
  taskStatusMap?: Record<string, TaskCardType["status"]>;
  showDetail?: boolean;
};

export default function WorkspaceColumn({
  title,
  tasks,
  selectedTaskId,
  onSelectTask,
  onStatusChange,
  taskStatusMap = {},
  showDetail = true,
}: WorkspaceColumnProps) {
  const [internalSelectedTaskId, setInternalSelectedTaskId] = useState<string | null>(tasks[0]?.task_id ?? null);
  const effectiveSelectedTaskId = selectedTaskId ?? internalSelectedTaskId;
  const setSelectedTask = onSelectTask ?? setInternalSelectedTaskId;

  const selectedTask = tasks.find((task) => task.task_id === effectiveSelectedTaskId) ?? tasks[0] ?? null;

  // Apply status overrides from taskStatusMap
  const selectedTaskWithStatus = selectedTask ? {
    ...selectedTask,
    status: taskStatusMap[selectedTask.task_id] || selectedTask.status,
  } : null;

  // Sort tasks: active tasks first, finished/dismissed at bottom
  const sortedTasks = [...tasks].sort((a, b) => {
    const statusA = taskStatusMap[a.task_id] || a.status;
    const statusB = taskStatusMap[b.task_id] || b.status;
    
    const isAFinished = statusA === "finished" || statusA === "dismissed";
    const isBFinished = statusB === "finished" || statusB === "dismissed";
    
    if (isAFinished && !isBFinished) return 1;
    if (!isAFinished && isBFinished) return -1;
    return 0;
  });

  return (
    <section className="flex rounded-3xl border border-slate-200 bg-white/85 shadow-sm lg:h-full lg:min-h-0 lg:flex-col lg:overflow-hidden">
      <div className="border-b border-slate-200 px-4 py-2.5">
        <div className="text-sm font-semibold text-slate-700">{title}</div>
        <div className="mt-0.5 text-xs text-slate-500">
        </div>
      </div>
      <div className="flex flex-col gap-3 p-3 lg:min-h-0 lg:flex-1 lg:overflow-hidden">
        {tasks.length > 0 ? (
          <>
            {showDetail ? (
              <div className="grid gap-3 lg:min-h-0 lg:flex-1 lg:grid-cols-[minmax(280px,0.8fr)_minmax(0,1.2fr)] lg:overflow-hidden">
                <section className="flex rounded-2xl border border-slate-200 bg-slate-50 lg:min-h-0 lg:flex-col lg:overflow-hidden">
                  <div className="grid gap-2.5 p-3 lg:min-h-0 lg:flex-1 lg:overflow-y-auto">
                    {sortedTasks.map((task) => {
                      const taskWithStatus = {
                        ...task,
                        status: taskStatusMap[task.task_id] || task.status,
                      };
                      return (
                        <TaskCard
                          key={task.task_id}
                          task={taskWithStatus}
                          selected={selectedTask?.task_id === task.task_id}
                          onSelect={() => setSelectedTask(task.task_id)}
                        />
                      );
                    })}
                  </div>
                </section>

                {selectedTaskWithStatus ? (
                  <section className="flex h-full lg:min-h-0 lg:flex-1 lg:overflow-hidden">

                    <div className="flex h-full flex-col gap-4 p-4 lg:min-h-0 lg:flex-1 lg:overflow-y-auto">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                            {selectedTaskWithStatus.section}
                          </span>
                          <span className="text-xs text-slate-400">Selected task</span>
                        </div>
                        <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ${
                          selectedTaskWithStatus.status === "finished" 
                            ? "bg-green-100 text-green-700"
                            : selectedTaskWithStatus.status === "dismissed"
                            ? "bg-gray-100 text-gray-700"
                            : "bg-blue-100 text-blue-700"
                        }`}>
                          {selectedTaskWithStatus.status}
                        </span>
                      </div>

                      <div>
                        <div className="text-lg font-semibold text-slate-900">{selectedTaskWithStatus.title}</div>
                        <p className="mt-1 text-sm text-slate-600">{selectedTaskWithStatus.why_it_matters}</p>
                      </div>

                      <div className="flex min-h-0 flex-1 flex-col justify-between gap-4">
                        <div className="space-y-3">
                          <div>
                            <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">First step</div>
                            <div className="text-sm text-slate-700">{selectedTaskWithStatus.first_step}</div>
                          </div>

                          <div>
                            <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">Hint</div>
                            <div className="text-sm text-slate-700">{selectedTaskWithStatus.hint}</div>
                          </div>
                        </div>

                        <div className="bg-white p-3">
                          <div className="mb-2 text-xs uppercase tracking-wide text-slate-500">Tools</div>
                          <div className="flex flex-wrap gap-2">
                            {selectedTaskWithStatus.tools.map((tool) => (
                              <span
                                key={tool}
                                className="rounded-full border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs text-slate-700"
                              >
                                {tool}
                              </span>
                            ))}
                          </div>

                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <button
                              type="button"
                              onClick={() => onStatusChange?.(selectedTaskWithStatus.task_id, "finished")}
                              className={`rounded-lg py-2 text-sm font-medium transition ${
                                selectedTaskWithStatus.status === "finished"
                                  ? "bg-green-200 text-green-800"
                                  : "bg-green-100 text-green-700 hover:bg-green-200"
                              }`}
                            >
                              ✓ Finished
                            </button>
                            <button
                              type="button"
                              onClick={() => onStatusChange?.(selectedTaskWithStatus.task_id, "dismissed")}
                              className={`rounded-lg py-2 text-sm font-medium transition ${
                                selectedTaskWithStatus.status === "dismissed"
                                  ? "bg-gray-200 text-gray-800"
                                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                              }`}
                            >
                              ✕ Dismissed
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </section>
                ) : null}
              </div>
            ) : (
              <section className="flex lg:min-h-0 lg:flex-1 lg:overflow-hidden">
                <div className="grid gap-2.5 p-3 lg:min-h-0 lg:flex-1 lg:overflow-y-auto">
                  {tasks.map((task) => (
                    <TaskCard
                      key={task.task_id}
                      task={task}
                      selected={selectedTask?.task_id === task.task_id}
                      onSelect={() => setSelectedTask(task.task_id)}
                    />
                  ))}
                </div>
              </section>
            )}
          </>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-300 p-4 text-sm text-slate-500">
            Nothing here yet.
          </div>
        )}
      </div>
    </section>
  );
}
