import { TaskCard } from "../lib/api";

const sectionLabelMap = {
  now: "Now",
  ready: "Ready",
  later: "Later",
};

type TaskCardProps = {
  task: TaskCard;
  selected: boolean;
  onSelect: () => void;
};

export default function TaskCard({ task, selected, onSelect }: TaskCardProps) {
  const statusColorMap = {
    now: "bg-blue-100 text-blue-700",
    ready: "bg-blue-100 text-blue-700",
    later: "bg-blue-100 text-blue-700",
    finished: "bg-green-100 text-green-700",
    dismissed: "bg-gray-100 text-gray-700",
  };

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-2xl border p-3 text-left transition ${
        selected
          ? "border-slate-900 bg-white shadow-sm"
          : "border-slate-200 bg-slate-50 hover:border-slate-300"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${statusColorMap[task.status]}`}>
              {task.status}
            </span>
            {selected ? <span className="text-xs text-slate-500">Selected</span> : null}
          </div>
          <div className="text-sm font-semibold text-slate-800">{task.title}</div>
          <div className="mt-1 line-clamp-2 text-xs text-slate-600">{task.first_step}</div>
        </div>
        <div className="pt-0.5 text-sm font-medium text-slate-400">→</div>
      </div>
    </button>
  );
}
