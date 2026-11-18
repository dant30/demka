import { useId, useState } from 'react';

export default function Tabs({
  tabs = [],
  value,
  defaultValue,
  onChange,
  className = '',
  tabListClassName = '',
  panelClassName = '',
  children,
}) {
  const generatedId = useId();
  const [internalValue, setInternalValue] = useState(
    defaultValue ?? tabs[0]?.value,
  );
  const selectedValue = value !== undefined ? value : internalValue;

  const selectTab = (tabValue) => {
    if (value === undefined) setInternalValue(tabValue);
    onChange?.(tabValue);
  };

  const handleKeyDown = (event, index) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();

    let nextIndex = index;
    if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = tabs.length - 1;

    const nextTab = tabs[nextIndex];
    if (nextTab?.disabled) return;
    selectTab(nextTab.value);
    document.getElementById(`${generatedId}-${nextIndex}`)?.focus();
  };

  const selectedTab = tabs.find((tab) => tab.value === selectedValue);
  const panel = typeof selectedTab?.content === 'function'
    ? selectedTab.content()
    : selectedTab?.content;

  return (
    <div className={className}>
      <div
        role="tablist"
        className={`!flex-nowrap !gap-0 flex w-full min-w-0 max-w-full touch-pan-x overscroll-x-contain overflow-x-auto border-b border-slate-200 ${tabListClassName}`}
      >
        {tabs.map((tab, index) => {
          const selected = tab.value === selectedValue;
          return (
            <button
              key={tab.value}
              id={`${generatedId}-${index}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`${generatedId}-panel`}
              tabIndex={selected ? 0 : -1}
              disabled={tab.disabled}
              onClick={() => selectTab(tab.value)}
              onKeyDown={(event) => handleKeyDown(event, index)}
              className={`shrink-0 whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                selected
                  ? 'border-brand-600 text-brand-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              } disabled:cursor-not-allowed disabled:opacity-40`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div
        id={`${generatedId}-panel`}
        role="tabpanel"
        className={`pt-4 ${panelClassName}`}
      >
        {panel ?? children}
      </div>
    </div>
  );
}
