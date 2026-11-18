export default function DataTable({
  columns = [], rows = [], loading = false, empty = 'No data.',
  keyField = 'id', onRowClick, caption = 'Results', title,
}) {
  if (loading) {
    return (
      <div className="card" role="status" aria-busy="true" aria-label="Loading results">
        <div className="animate-pulse space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 bg-slate-100 rounded" />
          ))}
        </div>
      </div>
    );
  }

  const titleColumn = columns.find((column) => column.mobileTitle) || columns[0];
  const detailColumns = columns.filter((column) => column !== titleColumn);

  const renderValue = (column, row) => {
    const value = column.render ? column.render(row) : row[column.key];
    return value === null || value === undefined || value === '' ? '—' : value;
  };

  const handleCardClick = (event, row) => {
    if (!onRowClick || event.target.closest('a, button, input, select, textarea')) return;
    onRowClick(row);
  };

  const handleCardKeyDown = (event, row) => {
    if (!onRowClick || event.target !== event.currentTarget) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onRowClick(row);
    }
  };

  return (
    <div className="card data-table-shell p-0 overflow-hidden">
      {title && <h2 className="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">{title}</h2>}
      <div className="mobile-data-list sm:hidden" aria-label={`${caption} list`}>
        {rows.length === 0 ? (
          <p className="mobile-data-empty">{empty}</p>
        ) : rows.map((row, index) => (
          <article
            key={row[keyField] ?? index}
            className={`mobile-data-card ${onRowClick ? 'mobile-data-card--interactive' : ''}`}
            onClick={(event) => handleCardClick(event, row)}
            onKeyDown={(event) => handleCardKeyDown(event, row)}
            tabIndex={onRowClick ? 0 : undefined}
            aria-label={onRowClick ? `Open ${caption} ${row[titleColumn?.key] ?? ''}` : undefined}
          >
            <div className="mobile-data-title">
              {titleColumn ? renderValue(titleColumn, row) : `Item ${index + 1}`}
            </div>
            {detailColumns.length > 0 && (
              <dl className="mobile-data-fields">
                {detailColumns.map((column) => (
                  <div key={column.key} className={`mobile-data-field ${column.mobileFullWidth ? 'col-span-2' : ''}`}>
                    <dt>{column.label}</dt>
                    <dd className={column.align === 'right' ? 'text-right tabular-nums' : ''}>
                      {renderValue(column, row)}
                    </dd>
                  </div>
                ))}
              </dl>
            )}
          </article>
        ))}
      </div>

      <div className="hidden overflow-x-auto overscroll-x-contain sm:block">
        <table className="table min-w-[38rem]">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} scope="col" className={c.align === 'right' ? 'text-right' : ''}>
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-10 text-slate-500">
                  {empty}
                </td>
              </tr>
            ) : (
              rows.map((row, index) => (
                <tr
                  key={row[keyField] ?? index}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  onKeyDown={onRowClick ? (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      onRowClick(row);
                    }
                  } : undefined}
                  tabIndex={onRowClick ? 0 : undefined}
                  className={onRowClick ? 'cursor-pointer' : ''}
                >
                  {columns.map((c) => (
                    <td key={c.key} className={c.align === 'right' ? 'text-right' : ''}>
                      {renderValue(c, row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}