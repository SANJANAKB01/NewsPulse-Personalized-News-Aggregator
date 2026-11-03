import { useState } from "react";
import { Search, X } from "lucide-react";

interface Props {
  onSearch: (q: string) => void;
  initialValue?: string;
  placeholder?: string;
  className?: string;
}

export default function SearchBar({ onSearch, initialValue = "", placeholder = "Search articles...", className = "" }: Props) {
  const [value, setValue] = useState(initialValue);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(value.trim());
  };

  return (
    <form onSubmit={submit} className={`relative ${className}`}>
      <Search size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="input pl-10 pr-10"
      />
      {value && (
        <button
          type="button"
          onClick={() => { setValue(""); onSearch(""); }}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
        >
          <X size={14} />
        </button>
      )}
    </form>
  );
}
