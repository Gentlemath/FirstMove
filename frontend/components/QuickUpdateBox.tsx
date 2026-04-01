export default function QuickUpdateBox() {
  return (
    <section className="border-2 border-slate-300 rounded-2xl bg-white/80 shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700">
        Quick update
      </div>
      <div className="space-y-3 p-4">
        <input
          className="w-full rounded-2xl border-2 border-slate-200 bg-slate-50 p-3 text-sm"
          defaultValue="Urgent: add meeting follow-up email and move reading later"
        />
        <button className="w-full rounded-xl border-2 border-slate-400 bg-white py-2.5 text-sm font-medium text-slate-800">
          Update workspace
        </button>
      </div>
    </section>
  );
}
