interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export default function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-champagne-700 mb-2 tracking-wide">
          {label}
        </label>
      )}
      <input
        className={`
          w-full px-4 py-3 bg-white border rounded-xl
          text-champagne-800 placeholder-champagne-400
          transition-all duration-300 ease-out
          focus:outline-none focus:ring-2 focus:ring-gold-200 focus:border-gold-400
          hover:border-champagne-400
          ${error ? 'border-red-300 focus:ring-red-200 focus:border-red-400' : 'border-champagne-200'}
          ${className}
        `}
        {...props}
      />
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </div>
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export function Textarea({ label, error, className = '', ...props }: TextareaProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-champagne-700 mb-2 tracking-wide">
          {label}
        </label>
      )}
      <textarea
        className={`
          w-full px-4 py-3 bg-white border rounded-xl
          text-champagne-800 placeholder-champagne-400
          transition-all duration-300 ease-out
          focus:outline-none focus:ring-2 focus:ring-gold-200 focus:border-gold-400
          hover:border-champagne-400 resize-none
          ${error ? 'border-red-300 focus:ring-red-200 focus:border-red-400' : 'border-champagne-200'}
          ${className}
        `}
        {...props}
      />
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </div>
  );
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string | number; label: string }[];
}

export function Select({ label, error, options, className = '', ...props }: SelectProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-champagne-700 mb-2 tracking-wide">
          {label}
        </label>
      )}
      <select
        className={`
          w-full px-4 py-3 bg-white border rounded-xl
          text-champagne-800 appearance-none cursor-pointer
          transition-all duration-300 ease-out
          focus:outline-none focus:ring-2 focus:ring-gold-200 focus:border-gold-400
          hover:border-champagne-400
          ${error ? 'border-red-300 focus:ring-red-200 focus:border-red-400' : 'border-champagne-200'}
          ${className}
        `}
        style={{
          backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%239A8A6E' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
          backgroundPosition: 'left 0.75rem center',
          backgroundRepeat: 'no-repeat',
          backgroundSize: '1.5em 1.5em',
          paddingLeft: '2.5rem',
        }}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </div>
  );
}
