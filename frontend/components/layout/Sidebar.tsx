"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx, ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import {
  LayoutDashboard,
  Calculator,
  UploadCloud,
  History,
  Cpu,
  Activity,
  Truck,
  X,
} from "lucide-react";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Predict Single", href: "/predict", icon: Calculator },
  { name: "Batch Predict", href: "/batch", icon: UploadCloud },
  { name: "Prediction History", href: "/history", icon: History },
  { name: "Model Info", href: "/models", icon: Cpu },
  { name: "MLOps Monitoring", href: "/monitoring", icon: Activity },
];

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform duration-200 dark:border-slate-800 dark:bg-slate-900 lg:static lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand Header */}
        <div className="flex h-16 items-center justify-between border-b border-slate-100 px-6 dark:border-slate-800">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white shadow-sm">
              <Truck className="h-5 w-5" />
            </div>
            <div>
              <span className="block font-bold text-slate-900 dark:text-white text-base leading-tight">
                FreightRate
              </span>
              <span className="block text-[11px] font-medium tracking-wider text-blue-600 dark:text-blue-400 uppercase">
                Predictor ML
              </span>
            </div>
          </Link>
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 lg:hidden"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Nav links */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-200"
                )}
              >
                <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-400")} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>

        {/* Footer Info */}
        <div className="border-t border-slate-100 p-4 dark:border-slate-800">
          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800/50">
            <span className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Enterprise ML Service
            </span>
            <span className="block text-[11px] text-slate-500 dark:text-slate-400">
              v1.0.0 • LightGBM / CatBoost / XGB
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}
