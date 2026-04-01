type TaskInputBoxProps = {
  value: string;
  onChange: (value: string) => void;
  onGenerate: () => void;
  generated?: boolean;
  compact?: boolean;
  isGenerating?: boolean;
};

export default function TaskInputBox({
  value,
  onChange,
  onGenerate,
  generated = false,
  compact = false,
  isGenerating = false,
}: TaskInputBoxProps) {
  return (
    <section className="flex flex-col rounded-3xl border border-slate-200 bg-white/85 shadow-sm lg:min-h-0 lg:flex-1">
      <div className="border-b border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">
        What else do you want to begin today?
      </div>
      <div className="flex flex-1 flex-col gap-3 p-3 lg:min-h-0">
        <textarea
          className={`w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 outline-none transition focus:border-slate-400 ${
            compact ? "h-28 lg:flex-1 lg:min-h-[150px]" : "h-36 lg:flex-1 lg:min-h-[220px]"
          }`}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={isGenerating}
        />
        <button
          type="button"
          onClick={onGenerate}
          disabled={isGenerating}
          className="w-full rounded-xl bg-blue-300 py-2.5 text-sm font-medium text-white transition hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? "Generating..." : generated ? "Refresh workspace" : "Generate workspace"}
        </button>
      </div>
    </section>
  );
}
