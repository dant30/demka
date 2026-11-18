import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from './client';
import { endpoints } from './endpoints';
import { useToast } from '@/components/ui/Toast';

function payloadRequestConfig(payload) {
  return typeof FormData !== 'undefined' && payload instanceof FormData
    ? { headers: { 'Content-Type': 'multipart/form-data' } }
    : undefined;
}

// ---- Generic helpers ---------------------------------------
export function useList(key, url, params = {}, opts = {}) {
  return useQuery({
    queryKey: [key, params],
    queryFn: async () => (await api.get(url, { params })).data,
    staleTime: 30_000,
    ...opts,
  });
}

export function useDetail(key, url, id, opts = {}) {
  return useQuery({
    queryKey: [key, id],
    queryFn: async () => (await api.get(url)).data,
    enabled: !!id && !!url,
    ...opts,
  });
}

export function useCreate(key, url, { onSuccess, invalidate = [] } = {}) {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: async (payload) =>
      (await api.post(url, payload, payloadRequestConfig(payload))).data,
    onSuccess: (data) => {
      invalidate.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
      onSuccess?.(data);
    },
    onError: (err) => toast.error(extractError(err)),
  });
}

export function useUpdate(key, urlFn, { onSuccess, invalidate = [] } = {}) {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: async ({ id, payload }) =>
      (await api.patch(urlFn(id), payload, payloadRequestConfig(payload))).data,
    onSuccess: (data) => {
      invalidate.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
      onSuccess?.(data);
    },
    onError: (err) => toast.error(extractError(err)),
  });
}

export function useDelete(key, urlFn, { onSuccess, invalidate = [] } = {}) {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: async (id) => (await api.delete(urlFn(id))).data,
    onSuccess: (_, id) => {
      invalidate.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
      onSuccess?.(id);
    },
    onError: (err) => toast.error(extractError(err)),
  });
}

export function useAction(key, urlFn, { onSuccess, invalidate = [] } = {}) {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: async ({ id, ...payload }) => (await api.post(urlFn(id), payload)).data,
    onSuccess: (data) => {
      invalidate.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
      onSuccess?.(data);
    },
    onError: (err) => toast.error(extractError(err)),
  });
}

// ---- Domain-specific hooks ---------------------------------
export function useDashboard(opts = {}) {
  return useQuery({
    queryKey: ['reporting-dashboard'],
    queryFn: async () => (await api.get(endpoints.reporting.dashboard)).data,
    staleTime: 30_000,
    refetchInterval: 60_000,
    ...opts,
  });
}

export function useProductLookup() {
  return useMutation({
    mutationFn: async ({ sku, barcode, part_number }) => {
      const { data } = await api.get(endpoints.inventory.productLookup, {
        params: sku ? { sku } : part_number ? { part_number } : { barcode },
      });
      return data;
    },
  });
}

export function useProductImport() {
  return useMutation({
    mutationFn: async ({ file, mode = 'preview', skipErrors = false }) => {
      const form = new FormData();
      form.append('file', file);
      form.append('mode', mode);
      form.append('skip_errors', skipErrors ? 'true' : 'false');
      const { data } = await api.post(endpoints.inventory.productImport, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
  });
}

export async function downloadProductTemplate() {
  const { data } = await api.get(endpoints.inventory.productImportTemplate, {
    responseType: 'blob',
  });
  const url = URL.createObjectURL(data);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'demka_product_template.xlsx';
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function useSalePreview() {
  return useMutation({
    mutationFn: async (payload) => (await api.post(endpoints.sales.preview, payload)).data,
  });
}

export function useCreateSale() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => (await api.post(endpoints.sales.list, payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sales'] });
      qc.invalidateQueries({ queryKey: ['stock-levels'] });
      qc.invalidateQueries({ queryKey: ['reporting-dashboard'] });
    },
  });
}

export function useApplyPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ saleId, ...payload }) =>
      (await api.post(endpoints.sales.applyPayment(saleId), payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sales'] });
      qc.invalidateQueries({ queryKey: ['reporting-dashboard'] });
    },
  });
}

export function useMpesaStkPush() {
  return useMutation({
    mutationFn: async (payload) => (await api.post(endpoints.payments.stkPush, payload)).data,
  });
}

export function useQueueReceipt() {
  return useMutation({
    mutationFn: async (saleId) =>
      (await api.post(endpoints.printing.queueReceipt, { sale: saleId })).data,
  });
}

export function useEscposPayload(jobId) {
  return useQuery({
    queryKey: ['escpos', jobId],
    queryFn: async () => (await api.get(endpoints.printing.jobEscpos(jobId))).data,
    enabled: !!jobId,
  });
}

export function useReportEscposResult() {
  return useMutation({
    mutationFn: async ({ jobId, success, error }) =>
      (await api.post(endpoints.printing.jobReportResult(jobId), { success, error })).data,
  });
}

export function useSystemHealth(opts = {}) {
  return useQuery({
    queryKey: ['system-health'],
    queryFn: async () => (await api.get(endpoints.auth.me)).data,
    staleTime: 15_000,
    refetchInterval: 60_000,
    retry: false,
    ...opts,
  });
}