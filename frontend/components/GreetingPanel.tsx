import FixedBlocks from "./FixedBlocks";
import { FixedBlock } from "../lib/types";

type GreetingPanelProps = {
  blocks: FixedBlock[];
  isLoading?: boolean;
};

export default function GreetingPanel({ blocks, isLoading = false }: GreetingPanelProps) {
  if (isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white/85 shadow-sm lg:h-full lg:min-h-0">
        <div className="border-b border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">
          Good morning
        </div>
        <div className="flex items-center justify-center p-8">
          <div className="text-sm text-slate-500">Loading calendar...</div>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white/85 shadow-sm lg:h-full lg:min-h-0">
      <div className="border-b border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">
        Good morning
      </div>
      <div className="space-y-4 p-4">
        {blocks.length > 0 && (
          <p className="text-sm text-slate-700 md:text-base">
            You already have <span className="font-semibold">{blocks.length} fixed blocks</span> today.
          </p>
        )}
        <FixedBlocks blocks={blocks} />
      </div>
    </section>
  );
}
