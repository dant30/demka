import { Children, forwardRef, isValidElement, useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

const Select = forwardRef(function Select(
  {
    label,
    error,
    hint,
    helperText,
    children,
    options,
    searchable = false,
    placeholder = 'Select an option',
    className = '',
    id,
    value,
    defaultValue = '',
    name,
    required,
    disabled,
    onChange,
    onValueChange,
    ...buttonProps
  }, ref
) {
  const generatedId = useId();
  const fieldId = id || generatedId;
  const listboxId = `${fieldId}-options`;
  const containerRef = useRef(null);
  const triggerRef = useRef(null);
  const listboxRef = useRef(null);
  const searchRef = useRef(null);
  const optionRefs = useRef([]);
  const [open, setOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [internalValue, setInternalValue] = useState(defaultValue);
  const [menuPosition, setMenuPosition] = useState(null);
  const selectedValue = value === undefined ? internalValue : value;

  const normalizedOptions = options
    ? options.map((option) => typeof option === 'string'
      ? { value: option, label: option }
      : { ...option, value: String(option.value) })
    : Children.toArray(children)
      .filter((child) => isValidElement(child) && child.type === 'option')
      .map((child) => ({
        value: String(child.props.value ?? child.props.children ?? ''),
        label: child.props.children,
        disabled: child.props.disabled,
      }));

  const search = searchTerm.trim().toLowerCase();
  const filteredOptions = normalizedOptions.filter((option) => (
    !search
    || String(option.label).toLowerCase().includes(search)
    || String(option.value).toLowerCase().includes(search)
    || String(option.sublabel || '').toLowerCase().includes(search)
  ));
  const selectedOption = normalizedOptions.find((option) => String(option.value) === String(selectedValue));
  const selectedIndex = filteredOptions.findIndex((option) => String(option.value) === String(selectedValue));
  const [highlightedIndex, setHighlightedIndex] = useState(Math.max(0, selectedIndex));

  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutsideClick = (event) => {
      if (
        !containerRef.current?.contains(event.target)
        && !listboxRef.current?.contains(event.target)
      ) setOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') {
        setOpen(false);
        setSearchTerm('');
      }
    };
    document.addEventListener('mousedown', closeOnOutsideClick);
    document.addEventListener('keydown', closeOnEscape);
    if (searchable) searchRef.current?.focus();
    return () => {
      document.removeEventListener('mousedown', closeOnOutsideClick);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open, searchable]);

  useLayoutEffect(() => {
    if (!open || disabled) return undefined;

    const positionMenu = () => {
      const trigger = triggerRef.current;
      if (!trigger) return;

      const rect = trigger.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom - 8;
      const spaceAbove = rect.top - 8;
      const openAbove = spaceBelow < 180 && spaceAbove > spaceBelow;
      const availableHeight = openAbove ? spaceAbove : spaceBelow;
      const maxHeight = Math.max(80, Math.min(256, availableHeight - 8));
      const width = Math.min(rect.width, window.innerWidth - 16);
      const left = Math.max(8, Math.min(rect.left, window.innerWidth - width - 8));

      setMenuPosition({
        position: 'fixed',
        top: openAbove ? Math.max(8, rect.top - maxHeight - 4) : rect.bottom + 4,
        left,
        right: 'auto',
        width,
        maxHeight,
        marginTop: 0,
        zIndex: 1100,
      });
    };

    positionMenu();
    window.addEventListener('resize', positionMenu);
    window.addEventListener('scroll', positionMenu, true);
    return () => {
      window.removeEventListener('resize', positionMenu);
      window.removeEventListener('scroll', positionMenu, true);
    };
  }, [open, disabled]);

  useEffect(() => {
    if (selectedIndex >= 0) setHighlightedIndex(selectedIndex);
  }, [selectedIndex]);

  useEffect(() => {
    if (open) optionRefs.current[highlightedIndex]?.scrollIntoView({ block: 'nearest' });
  }, [highlightedIndex, open]);

  const getAvailableIndex = (start, direction) => {
    for (let index = start; index >= 0 && index < filteredOptions.length; index += direction) {
      if (!filteredOptions[index].disabled) return index;
    }
    return -1;
  };

  const openMenu = (index = Math.max(0, selectedIndex), direction = 1) => {
    const firstAvailable = getAvailableIndex(index, direction);
    setHighlightedIndex(firstAvailable >= 0 ? firstAvailable : 0);
    setOpen(true);
  };

  const choose = (option) => {
    if (option.disabled) return;
    if (value === undefined) setInternalValue(option.value);
    onValueChange?.(option.value);
    if (options !== undefined) onChange?.(option.value);
    else onChange?.({
      target: { name, value: option.value },
      currentTarget: { name, value: option.value },
    });
    setOpen(false);
    setSearchTerm('');
  };

  const handleTriggerKeyDown = (event) => {
    if (disabled) return;
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const direction = event.key === 'ArrowDown' ? 1 : -1;
      if (!open) {
        const start = selectedIndex >= 0
          ? selectedIndex + direction
          : direction === 1 ? 0 : filteredOptions.length - 1;
        openMenu(start, direction);
        return;
      }
      const nextIndex = getAvailableIndex(highlightedIndex + direction, direction);
      if (nextIndex >= 0) setHighlightedIndex(nextIndex);
      return;
    }
    if (event.key === 'Home' || event.key === 'End') {
      event.preventDefault();
      const index = getAvailableIndex(event.key === 'Home' ? 0 : filteredOptions.length - 1, event.key === 'Home' ? 1 : -1);
      if (index >= 0) {
        setHighlightedIndex(index);
        setOpen(true);
      }
      return;
    }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (open) {
        const option = filteredOptions[highlightedIndex];
        if (option) choose(option);
      } else openMenu();
    }
  };

  const handleSearchKeyDown = (event) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const direction = event.key === 'ArrowDown' ? 1 : -1;
      const index = getAvailableIndex(highlightedIndex + direction, direction);
      if (index >= 0) setHighlightedIndex(index);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const option = filteredOptions[highlightedIndex];
      if (option) choose(option);
    }
  };

  return (
    <div ref={containerRef} className={`relative min-w-0 ${className}`}>
      {label && <label className="label" htmlFor={fieldId}>{label}{required && <span className="ml-1 text-red-600">*</span>}</label>}
      <button
        {...buttonProps}
        ref={(node) => {
          triggerRef.current = node;
          if (typeof ref === 'function') ref(node);
          else if (ref) ref.current = node;
        }}
        id={fieldId}
        type="button"
        role="combobox"
        disabled={disabled}
        aria-expanded={open}
        aria-controls={listboxId}
        aria-haspopup="listbox"
        aria-activedescendant={open ? `${listboxId}-${highlightedIndex}` : undefined}
        aria-invalid={error ? 'true' : undefined}
        aria-required={required || undefined}
        aria-describedby={error ? `${fieldId}-error` : hint || helperText ? `${fieldId}-hint` : undefined}
        className={`input flex items-center justify-between gap-3 text-left ${error ? 'input-error' : ''}`}
        onClick={() => open ? setOpen(false) : openMenu()}
        onKeyDown={handleTriggerKeyDown}
      >
        <span className={`min-w-0 truncate ${selectedOption ? 'text-slate-900' : 'text-slate-400'}`}>
          {selectedOption?.label || placeholder}
        </span>
        <span aria-hidden="true" className={`shrink-0 text-slate-500 transition-transform ${open ? 'rotate-180' : ''}`}>
          ▾
        </span>
      </button>
      {name && <input type="hidden" name={name} value={selectedValue ?? ''} disabled={disabled} />}
      {open && !disabled && createPortal(
        <div
          ref={listboxRef}
          id={listboxId}
          role="listbox"
          aria-label={label || 'Options'}
          className="select-menu"
          style={menuPosition || { position: 'fixed', left: 8, top: 8, zIndex: 1100 }}
        >
          {searchable && (
            <input
              ref={searchRef}
              type="search"
              value={searchTerm}
              onChange={(event) => { setSearchTerm(event.target.value); setHighlightedIndex(0); }}
              onKeyDown={handleSearchKeyDown}
              placeholder="Search options..."
              aria-label={`Search ${label || 'options'}`}
              className="input input-sm mb-1"
            />
          )}
          {filteredOptions.length ? filteredOptions.map((option, index) => (
            <button
              ref={(element) => { optionRefs.current[index] = element; }}
              key={`${option.value}-${index}`}
              id={`${listboxId}-${index}`}
              type="button"
              role="option"
              aria-selected={String(option.value) === String(selectedValue)}
              disabled={option.disabled}
              onMouseEnter={() => !option.disabled && setHighlightedIndex(index)}
              onClick={() => choose(option)}
              className={`select-option ${highlightedIndex === index ? 'select-option--active' : ''} ${String(option.value) === String(selectedValue) ? 'select-option--selected' : ''}`}
            >
              <span className="min-w-0">
                <span className="block truncate">{option.label}</span>
                {option.sublabel && <span className="block truncate text-xs font-normal text-slate-500">{option.sublabel}</span>}
              </span>
              {String(option.value) === String(selectedValue) && <span aria-hidden="true" className="text-brand-600">✓</span>}
            </button>
          )) : <p className="px-3 py-2 text-sm text-slate-500">No options found.</p>}
        </div>,
        document.body,
      )}
      {error && <p id={`${fieldId}-error`} className="field-error">{error}</p>}
      {(hint || helperText) && !error && <p id={`${fieldId}-hint`} className="field-hint">{hint || helperText}</p>}
    </div>
  );
});

export default Select;