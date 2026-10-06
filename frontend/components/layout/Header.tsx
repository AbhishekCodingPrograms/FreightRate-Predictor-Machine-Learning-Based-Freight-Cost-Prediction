"use client";

import React, { useEffect, useState } from "react";
import { Menu, Database, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";
import { getHealth } from "../../lib/api/health";
import { HealthResponse } from "../../lib/types/api";

export interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const fetchHealthStatus = async () => {
      try {
        const res = await getHealth();
        if (isMounted) {
          setHealth(res);
          setError(false);
          setLoading(false);
        }
      } catch {
        if (isMounted) {
          setError(true);
          setHealth(null);
          setLoading(false);
        }
      }
    };

    fetchHealthStatus();
    const interval = setInterval(fetchHealthStatus, 30000); // 30s poll
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 lg:hidden"
          aria-label="Open Navigation Menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="text-base font-semibold text-slate-900 dark:text-slate-100 sm:text-lg">
          Spot Freight Rate Cost Predictor
        </h1>
      </div>

      {/* Health Badge status */}
      <div className="flex items-center gap-2 text-xs">
        {loading && !health && (
          <div className="flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-400">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            <span>Checking API...</span>
          </div>
        )}

        {!loading && health && (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-emerald-700 ring-1 ring-emerald-600/20 dark:bg-emerald-950/40 dark:text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span className="font-semibold">API Online</span>
            </div>
            <div
              className={`hidden sm:flex items-center gap-1.5 rounded-full px-2.5 py-1 ring-1 ${
                health.database_connected
                  ? "bg-blue-50 text-blue-700 ring-blue-700/20 dark:bg-blue-950/40 dark:text-blue-400"
                  : "bg-amber-50 text-amber-700 ring-amber-700/20 dark:bg-amber-950/40 dark:text-amber-400"
              }`}
            >
              <Database className="h-3.5 w-3.5" />
              <span>{health.database_connected ? "DB Connected" : "DB Offline"}</span>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-1.5 rounded-full bg-rose-50 px-3 py-1 font-medium text-rose-700 ring-1 ring-rose-600/20 dark:bg-rose-950/40 dark:text-rose-400">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>API Offline</span>
          </div>
        )}
      </div>
    </header>
  );
}
