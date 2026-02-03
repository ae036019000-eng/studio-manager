interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField: keyof T;
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
}

export default function Table<T>({
  columns,
  data,
  keyField,
  onRowClick,
  emptyMessage = 'אין נתונים להצגה',
}: TableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-champagne-300 text-5xl mb-4">◇</div>
        <p className="text-champagne-700 font-medium">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-champagne-200">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={`px-6 py-4 text-right text-sm font-semibold text-champagne-600 tracking-wide uppercase ${col.className || ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-champagne-100">
          {data.map((item) => (
            <tr
              key={String(item[keyField])}
              onClick={() => onRowClick?.(item)}
              className={`
                transition-all duration-300
                hover:bg-gradient-to-l hover:from-gold-50 hover:to-transparent
                ${onRowClick ? 'cursor-pointer' : ''}
              `}
            >
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={`px-6 py-5 text-sm text-champagne-800 ${col.className || ''}`}
                >
                  {col.render
                    ? col.render(item)
                    : String(item[col.key as keyof T] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
