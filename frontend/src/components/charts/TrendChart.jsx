import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const DEFAULT_COLORS = [
  '#2563eb',
  '#10b981',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
];

const CHART_TYPES = {
  line: LineChart,
  bar: BarChart,
  area: AreaChart,
  composed: ComposedChart,
};

const formatCompactNumber = (value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) return value;

  return new Intl.NumberFormat('en', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(number);
};

export default function TrendChart({
  data = [],
  xKey = 'date',
  series = [],
  type = 'line',

  // Formatting
  valueFormatter,
  axisFormatter = formatCompactNumber,
  labelFormatter,

  // Dimensions
  height = 280,

  // Display
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  showXAxis = true,
  showYAxis = true,

  // Axis configuration
  xAxisAngle = 0,
  yAxisWidth = 56,
  minTickGap = 24,

  // States
  loading = false,
  emptyMessage = 'No chart data available.',
  
  // Styling
  className = '',
  gridColor = '#e2e8f0',
  axisColor = '#64748b',

  // Advanced
  tooltipContent,
  tooltipCursor = true,
}) {
  const ChartComponent = CHART_TYPES[type] || LineChart;
  const hasData = Array.isArray(data) && data.length > 0;
  const hasSeries = Array.isArray(series) && series.length > 0;
  const yAxisIds = Array.from(new Set([
    'left',
    ...series.map((item) => item.yAxisId).filter((id) => id !== undefined && id !== null),
  ]));

  const formatValue = (value, item) => (
    valueFormatter ? valueFormatter(value, item) : formatCompactNumber(value)
  );
  const formatLabel = (label) => (labelFormatter ? labelFormatter(label) : label);

  if (loading) {
    return (
      <div
        className={`flex w-full items-center justify-center rounded-lg bg-slate-50 dark:bg-slate-800/50 ${className}`.trim()}
        style={{ height }}
        role="status"
        aria-label="Loading chart"
      >
        <div className="w-full space-y-4 px-6">
          <div className="flex h-36 items-end gap-3">
            {[45, 75, 55, 90, 65, 80, 50, 70].map((barHeight, index) => (
              <div
                key={index}
                className="flex-1 animate-pulse rounded-t-md bg-slate-200 dark:bg-slate-700"
                style={{ height: `${barHeight}%` }}
              />
            ))}
          </div>
          <div className="h-2 w-1/3 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          <span className="sr-only">Loading chart data...</span>
        </div>
      </div>
    );
  }

  if (!hasData || !hasSeries) {
    return (
      <div
        className={`flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 text-center dark:border-slate-700 dark:bg-slate-800/40 ${className}`.trim()}
        style={{ minHeight: height }}
        role="status"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-8 w-8 text-slate-400" stroke="currentColor" strokeWidth="1.5">
          <path d="M3 3v18h18M7 14l4-4 4 3 5-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{emptyMessage}</p>
        <p className="text-xs text-slate-400">Chart data will appear here when available.</p>
      </div>
    );
  }

  return (
    <div className={`w-full min-w-0 ${className}`.trim()} style={{ height }} role="img" aria-label="Trend chart">
      <ResponsiveContainer width="100%" height="100%">
        <ChartComponent
          data={data}
          margin={{ top: 8, right: 12, bottom: xAxisAngle ? 24 : 4, left: 0 }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />}

          {showXAxis && (
            <XAxis
              dataKey={xKey}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: axisColor }}
              minTickGap={minTickGap}
              interval="preserveStartEnd"
              angle={xAxisAngle}
              textAnchor={xAxisAngle ? 'end' : 'middle'}
              height={xAxisAngle ? 55 : 30}
              tickFormatter={formatLabel}
            />
          )}

          {showYAxis && yAxisIds.map((axisId, index) => (
            <YAxis
              key={axisId}
              yAxisId={axisId}
              orientation={index === 0 ? 'left' : 'right'}
              axisLine={false}
              tickLine={false}
              width={yAxisWidth}
              tick={{ fontSize: 11, fill: axisColor }}
              tickFormatter={axisFormatter}
            />
          ))}

          {showTooltip && (
            <Tooltip
              cursor={tooltipCursor ? { fill: 'rgba(148,163,184,0.08)' } : false}
              content={tooltipContent}
              formatter={formatValue}
              labelFormatter={formatLabel}
              contentStyle={{
                borderRadius: 10,
                border: '1px solid #e2e8f0',
                backgroundColor: '#ffffff',
                padding: '10px 12px',
                fontSize: 12,
                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
              }}
              labelStyle={{ color: '#334155', fontWeight: 600, marginBottom: 6 }}
            />
          )}

          {showLegend && series.length > 1 && (
            <Legend
              verticalAlign="bottom"
              height={30}
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            />
          )}

          {series.map((item, index) => {
            const color = item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
            const name = item.name || item.dataKey;
            const seriesType = type === 'composed' ? item.type || 'line' : type;
            const commonProps = {
              dataKey: item.dataKey,
              name,
              yAxisId: item.yAxisId ?? 'left',
              animationDuration: 500,
            };

            if (seriesType === 'bar') {
              return <Bar key={item.dataKey} {...commonProps} fill={color} radius={[4, 4, 0, 0]} maxBarSize={item.maxBarSize || 42} stackId={item.stackId} />;
            }

            if (seriesType === 'area') {
              return (
                <Area
                  key={item.dataKey}
                  {...commonProps}
                  type={item.curve || 'monotone'}
                  stroke={color}
                  fill={color}
                  fillOpacity={item.fillOpacity ?? 0.12}
                  strokeWidth={item.strokeWidth || 2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  connectNulls
                  stackId={item.stackId}
                />
              );
            }

            return (
              <Line
                key={item.dataKey}
                {...commonProps}
                type={item.curve || 'monotone'}
                stroke={color}
                strokeWidth={item.strokeWidth || 2}
                dot={item.dot ?? false}
                activeDot={{ r: 5 }}
                strokeDasharray={item.strokeDasharray}
                connectNulls
              />
            );
          })}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
}
