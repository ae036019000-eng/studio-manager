interface SearchFilterProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export default function SearchFilter({
  value,
  onChange,
  placeholder = 'חיפוש...',
}: SearchFilterProps) {
  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="
          w-full pl-12 pr-5 py-3 bg-white border border-champagne-200 rounded-xl
          text-champagne-800 placeholder-champagne-400
          transition-all duration-300 ease-out
          focus:outline-none focus:ring-2 focus:ring-gold-200 focus:border-gold-400
          hover:border-champagne-400
        "
      />
      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-champagne-600">
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </span>
    </div>
  );
}
