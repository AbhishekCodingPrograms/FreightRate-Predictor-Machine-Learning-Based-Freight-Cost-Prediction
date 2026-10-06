import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from "lucide-react";

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "error" | "success" | "warning" | "info";
  title?: string;
}

export function Alert({ className, variant = "info", title, children, ...props }: AlertProps) {
  const styles = {
    error: {
      container: "border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300",
      icon: <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />,
    },
    success: {
      container: "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300",
      icon: <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />,
    },
    warning: {
      container: "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-300",
      icon: <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />,
    },
    info: {
      container: "border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-900/50 dark:bg-blue-950/40 dark:text-blue-300",
      icon: <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />,
    },
  };

  const current = styles[variant];

  return (
    <div
      className={cn("flex gap-3 rounded-lg border p-4 text-sm shadow-sm transition-all", current.container, className)}
      role="alert"
      {...props}
    >
      <div className="shrink-0">{current.icon}</div>
      <div className="space-y-1">
        {title && <h5 className="font-semibold leading-tight">{title}</h5>}
        <div className="leading-relaxed opacity-90">{children}</div>
      </div>
    </div>
  );
}
