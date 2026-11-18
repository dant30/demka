import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { todayIso } from '@/utils/dates';

export function useTodayFieldRuns(user, { enabled = true } = {}) {
  const query = useQuery({
    queryKey: ['field-runs', user?.id, user?.role],
    queryFn: async () => {
      const today = todayIso();
      const params = { date_after: today, date_before: today };
      if (user?.role === 'FIELD_AGENT') params.agent = user.id;
      const { data } = await api.get(endpoints.routes.runs, { params });
      return data;
    },
    enabled: Boolean(user?.id) && enabled,
    refetchInterval: 30_000,
  });

  const runs = query.data?.results || query.data || [];
  return {
    ...query,
    runs,
    activeRuns: runs.filter((run) => run.status === 'IN_PROGRESS'),
    plannedRuns: runs.filter((run) => run.status === 'PLANNED'),
  };
}