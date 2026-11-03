import { Link } from "react-router-dom";
import { FileText } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-4 text-center">
      <div className="text-6xl font-bold text-slate-300 dark:text-slate-700">404</div>
      <div className="mt-4 flex items-center gap-2 text-slate-500">
        <FileText size={20} />
        <span>This page doesn't exist.</span>
      </div>
      <Link to="/" className="btn-primary mt-6">Back to dashboard</Link>
    </div>
  );
}
