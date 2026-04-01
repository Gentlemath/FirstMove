import { FixedBlock } from "../lib/types";

type FixedBlocksProps = {
  blocks: FixedBlock[];
  stacked?: boolean;
  compact?: boolean;
};

export default function FixedBlocks({
  blocks,
  stacked = false,
  compact = false,
}: FixedBlocksProps) {
  if (blocks.length === 0) {
    return (
      <div className={`${
        compact ? "p-3" : "p-4"
      }`}>
        <div className={`${compact ? "text-[13px]" : "text-sm"} text-slate-600 italic`}>
          All clear! You have a flexible day ahead.
        </div>
      </div>
    );
  }

  return (
    <div className={stacked ? "grid gap-3" : "grid gap-3 md:grid-cols-2"}>
      {blocks.map((block) => (
        <div
          key={block.id}
          className={`rounded-2xl border border-slate-200 bg-slate-50 ${
            compact ? "p-3" : "p-4"
          }`}
        >
          <div className={`${compact ? "text-[13px]" : "text-sm"} font-medium text-slate-800`}>
            {block.time} {block.title}
          </div>
          <div className={`mt-1 ${compact ? "text-[11px]" : "text-xs"} text-slate-500`}>
            {block.location ?? "Calendar event"}
          </div>

          {block.online_link ? (
            <div className="mt-2 text-[11px] text-indigo-600">
              <a href={block.online_link} target="_blank" rel="noreferrer">
                Join online meeting
              </a>
            </div>
          ) : null}

          {block.html_link ? (
            <div className="mt-2 text-[11px] text-indigo-600">
              <a href={block.html_link} target="_blank" rel="noreferrer">
                View on Google Calendar
              </a>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
