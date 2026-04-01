"use client";

import { useMemo } from "react";

export default function AppHeader() {
  const todayFormatted = useMemo(() => {
    const today = new Date();
    const dayName = today.toLocaleDateString("en-US", { weekday: "long" });
    const monthDay = today.toLocaleDateString("en-US", { month: "long", day: "numeric" });
    return `${dayName}, ${monthDay}`;
  }, []);

  return (
    <header className="px-1 py-1">
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">First Move</h1>
          <p className="mt-1 text-sm text-slate-600">Build your daily momentum</p>
        </div>
        <div className="text-sm text-slate-500">{todayFormatted}</div>
      </div>
    </header>
  );
}
