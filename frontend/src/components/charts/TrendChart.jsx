import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export default function TrendChart({
  data = [],
  xKey = 'date',
  series = [],
  type = 'line',
  valueFormatter,
  height = 260,
  emptyMessage = 'No chart data available.',
}) {
  if (!data.length) {
    return <div className="chart-empty" style={{ minHeight: height }}>{emptyMessage}</div>;
  }

  const Chart = type === 'bar' ? BarChart : LineChart;
  const formatValue = valueFormatter || ((value) => value);
  const formatAxisValue = (value) => {
    const number = Number(value);
    return Number.isFinite(number)
      ? new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(number)
      : value;
  };

  return (
    <div className="chart-canvas" style={{ height }} role="img" aria-label="Trend chart">
      <ResponsiveContainer width="100%" height="100%">
        <Chart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis
            dataKey={xKey}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 11, fill: '#64748b' }}
            minTickGap={24}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            width={56}
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickFormatter={formatAxisValue}
          />
          <Tooltip
            contentStyle={{ borderRadius: 6, borderColor: '#dbe3eb', fontSize: 12 }}
            formatter={(value, name) => [formatValue(value), name]}
            labelStyle={{ color: '#334155', fontWeight: 600 }}
          />
          {series.map((item) => type === 'bar' ? (
            <Bar
              key={item.dataKey}
              dataKey={item.dataKey}
              name={item.name || item.dataKey}
              fill={item.color || '#2563eb'}
              radius={[3, 3, 0, 0]}
              maxBarSize={40}
            />
          ) : (
            <Line
              key={item.dataKey}
              type="monotone"
              dataKey={item.dataKey}
              name={item.name || item.dataKey}
              stroke={item.color || '#2563eb'}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </Chart>
      </ResponsiveContainer>
    </div>
  );
}
