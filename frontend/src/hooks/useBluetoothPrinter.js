import { useState } from 'react';
import { isBluetoothSupported, printEscpos } from '@/services/bluetoothPrinter';
import { useEscposPayload, useReportEscposResult } from '@/api/queries';
import { storage } from '@/storage/localStorage';

/**
 * Field-agent workflow: fetch ESC/POS bytes for a job, push to BLE printer,
 * report result back to backend.
 */
export function useBluetoothPrinter() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const reportResult = useReportEscposResult();

  const printJob = async (jobId) => {
    setBusy(true);
    setError(null);
    try {
      if (!isBluetoothSupported()) {
        throw new Error('Bluetooth printing requires Chrome on Android.');
      }
      // Fetch bytes
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || '/api'}/printing/jobs/${jobId}/escpos/`,
        { headers: { Authorization: `Bearer ${storage.getItem('access_token')}` } }
      );
      if (!res.ok) throw new Error('Failed to fetch ESC/POS payload.');
      const { escpos_base64 } = await res.json();

      // Push to printer
      await printEscpos(escpos_base64);
      await reportResult.mutateAsync({ jobId, success: true });
      return true;
    } catch (err) {
      setError(err.message);
      try {
        await reportResult.mutateAsync({
          jobId, success: false, error: err.message,
        });
      } catch { /* ignore */ }
      return false;
    } finally {
      setBusy(false);
    }
  };

  return { printJob, busy, error, supported: isBluetoothSupported() };
}