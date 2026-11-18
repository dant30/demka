import { forwardRef, useEffect, useId, useRef, useState } from 'react';

const WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
const MONTHS = Array.from({ length: 12 }, (_, month) => (
  new Intl.DateTimeFormat('en', { month: 'long' }).format(new Date(2024, month, 1))
));

function parseDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return null;
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day
    ? date
    : null;
}

function toDateString(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

const DatePicker = forwardRef(function DatePicker({
  label,
  value = '',
  onChange,
  placeholder = 'Select date',
  minDate,
  maxDate,
  required = false,
  className = '',
  helperText,
  error,
  quickPresets = true,
  disabled = false,
  id,
  ariaLabel,
  name,
}, ref) {
  const generatedId = useId();
  const fieldId = id || generatedId;
  const containerRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [viewMode, setViewMode] = useState('days');
  const initialDate = parseDate(value) || new Date();
  const [viewYear, setViewYear] = useState(initialDate.getFullYear());
  const [viewMonth, setViewMonth] = useState(initialDate.getMonth());

  useEffect(() => {
    const selected = parseDate(value);
    if (selected) {
      setViewYear(selected.getFullYear());
      setViewMonth(selected.getMonth());
    }
  }, [value]);

  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutsideClick = (event) => {
      if (!containerRef.current?.contains(event.target)) setOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', closeOnOutsideClick);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('mousedown', closeOnOutsideClick);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open]);

  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const firstDay = new Date(viewYear, viewMonth, 1).getDay();
  const dayCells = [...Array(firstDay).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => i + 1)];
  const monthStart = toDateString(new Date(viewYear, viewMonth, 1));
  const monthEnd = toDateString(new Date(viewYear, viewMonth, daysInMonth));
  const canGoPrevious = !minDate || monthEnd > minDate;
  const canGoNext = !maxDate || monthStart < maxDate;
  const yearWindowStart = Math.floor(viewYear / 12) * 12;
  const years = Array.from({ length: 12 }, (_, index) => yearWindowStart + index);
  const displayValue = parseDate(value)?.toLocaleDateString('en-KE', {
    day: 'numeric', month: 'short', year: 'numeric',
  });

  const withinRange = (dateString) => (!minDate || dateString >= minDate)
    && (!maxDate || dateString <= maxDate);

  const chooseDate = (date) => {
    const dateString = toDateString(date);
    if (!withinRange(dateString)) return;
    onChange?.(dateString);
    setOpen(false);
    setViewMode('days');
  };

  const changeMonth = (amount) => {
    const next = new Date(viewYear, viewMonth + amount, 1);
    setViewYear(next.getFullYear());
    setViewMonth(next.getMonth());
  };

  const selectPreset = (preset) => {
    const target = new Date();
    if (preset === 'tomorrow') target.setDate(target.getDate() + 1);
    if (preset === 'weekend') {
      const daysUntilSaturday = (6 - target.getDay() + 7) % 7 || 7;
      target.setDate(target.getDate() + daysUntilSaturday);
    }
    if (preset === 'nextMonth') target.setMonth(target.getMonth() + 1, 1);
    const dateString = toDateString(target);
    if (!withinRange(dateString)) return;
    setViewYear(target.getFullYear());
    setViewMonth(target.getMonth());
    chooseDate(target);
  };

  const monthAvailable = (month) => {
    const start = toDateString(new Date(viewYear, month, 1));
    const end = toDateString(new Date(viewYear, month + 1, 0));
    return (!minDate || end >= minDate) && (!maxDate || start <= maxDate);
  };

  return (
    <div ref={containerRef} className={`relative min-w-0 ${className}`}>
      {label && (
        <label className="label" htmlFor={fieldId}>
          {label}{required && <span className="ml-1 text-red-600">*</span>}
        </label>
      )}
      <div className="relative flex min-w-0">
        <button
          ref={ref}
          id={fieldId}
          type="button"
          disabled={disabled}
          aria-label={ariaLabel || label || placeholder}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-invalid={error ? 'true' : undefined}
          aria-required={required || undefined}
          aria-describedby={error ? `${fieldId}-error` : helperText ? `${fieldId}-hint` : undefined}
          onClick={() => setOpen((current) => !current)}
          className={`input flex items-center justify-between gap-2 text-left ${value ? 'pr-10' : ''} ${error ? 'input-error' : ''} ${disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer hover:border-slate-400'}`}
        >
          <span className="flex min-w-0 items-center gap-2 truncate">
            <span aria-hidden="true" className="text-brand-600">▦</span>
            <span className={displayValue ? 'truncate text-slate-900' : 'truncate text-slate-400'}>
              {displayValue || placeholder}
            </span>
          </span>
          <span aria-hidden="true" className="shrink-0 text-xs text-slate-500">▾</span>
        </button>
        {value && !disabled && (
          <button type="button" aria-label="Clear date" className="date-picker-clear" onClick={() => onChange?.('')}>
            ×
          </button>
        )}
        {name && <input type="hidden" name={name} value={value} disabled={disabled} />}
      </div>
      {helperText && !error && <p id={`${fieldId}-hint`} className="field-hint">{helperText}</p>}
      {error && <p id={`${fieldId}-error`} className="field-error">{error}</p>}

      {open && !disabled && (
        <div role="dialog" aria-label={`${label || 'Date'} calendar`} className="date-picker-popover">
          {quickPresets && (
            <div className="grid grid-cols-4 gap-1 border-b border-slate-100 pb-3">
              {[
                ['Today', 'today'], ['Tomorrow', 'tomorrow'], ['Weekend', 'weekend'], ['Next month', 'nextMonth'],
              ].map(([presetLabel, preset]) => (
                <button key={preset} type="button" className="date-picker-preset" onClick={() => selectPreset(preset)}>
                  {presetLabel}
                </button>
              ))}
            </div>
          )}

          <div className="my-3 flex items-center justify-between gap-2">
            <button type="button" className="date-picker-nav" disabled={viewMode === 'days' && !canGoPrevious} aria-label="Previous month or year" onClick={() => viewMode === 'days' ? changeMonth(-1) : setViewYear((year) => year - 12)}>‹</button>
            <div className="flex items-center gap-1">
              {viewMode === 'days' && (
                <>
                  <button type="button" className="date-picker-heading" onClick={() => setViewMode('months')}>
                    {MONTHS[viewMonth]}
                  </button>
                  <button type="button" className="date-picker-heading" onClick={() => setViewMode('years')}>
                    {viewYear}
                  </button>
                </>
              )}
              {viewMode === 'months' && <span className="date-picker-heading">Choose month</span>}
              {viewMode === 'years' && <span className="date-picker-heading">Choose year</span>}
            </div>
            <button type="button" className="date-picker-nav" disabled={viewMode === 'days' && !canGoNext} aria-label="Next month or year" onClick={() => viewMode === 'days' ? changeMonth(1) : setViewYear((year) => year + 12)}>›</button>
          </div>

          {viewMode === 'days' && (
            <>
              <div className="grid grid-cols-7 text-center">
                {WEEKDAYS.map((day) => <span key={day} className="date-picker-weekday">{day}</span>)}
              </div>
              <div className="grid grid-cols-7 gap-1 text-center">
                {dayCells.map((day, index) => {
                  if (!day) return <span key={`blank-${index}`} />;
                  const date = new Date(viewYear, viewMonth, day);
                  const dateString = toDateString(date);
                  const isToday = dateString === toDateString(new Date());
                  const selected = dateString === value;
                  return (
                    <button
                      key={dateString}
                      type="button"
                      disabled={!withinRange(dateString)}
                      aria-label={date.toLocaleDateString('en-KE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
                      aria-pressed={selected}
                      onClick={() => chooseDate(date)}
                      className={`date-picker-day ${selected ? 'date-picker-day--selected' : ''} ${isToday && !selected ? 'date-picker-day--today' : ''}`}
                    >
                      {day}
                    </button>
                  );
                })}
              </div>
            </>
          )}

          {viewMode === 'months' && (
            <div className="grid grid-cols-3 gap-2">
              {MONTHS.map((month, index) => (
                <button key={month} type="button" disabled={!monthAvailable(index)} className="date-picker-period" onClick={() => { setViewMonth(index); setViewMode('days'); }}>
                  {month.slice(0, 3)}
                </button>
              ))}
            </div>
          )}

          {viewMode === 'years' && (
            <div className="grid grid-cols-3 gap-2">
              {years.map((year) => (
                <button key={year} type="button" disabled={(minDate && year < Number(minDate.slice(0, 4))) || (maxDate && year > Number(maxDate.slice(0, 4)))} className="date-picker-period" onClick={() => { setViewYear(year); setViewMode('months'); }}>
                  {year}
                </button>
              ))}
            </div>
          )}

          {viewMode === 'days' && (
            <button type="button" className="date-picker-today" onClick={() => {
              const today = new Date();
              setViewYear(today.getFullYear());
              setViewMonth(today.getMonth());
              chooseDate(today);
            }}>
              Today
            </button>
          )}
        </div>
      )}
    </div>
  );
});

export default DatePicker;
