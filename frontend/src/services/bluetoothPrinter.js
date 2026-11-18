/**
 * Web Bluetooth ESC/POS printer driver.
 *
 * Used by field agents to print receipts from their phones. The backend
 * renders ESC/POS bytes; this function pushes them over BLE.
 *
 * Compatible with most cheap 58mm BLE thermal printers
 * (Goojprt PT-210, Xprinter XP-P323B, etc.).
 */

const SERVICE_UUID = '000018f0-0000-1000-8000-00805f9b34fb';
const CHARACTERISTIC_UUID = '00002af1-0000-1000-8000-00805f9b34fb';

export function isBluetoothSupported() {
  return typeof navigator !== 'undefined' && 'bluetooth' in navigator;
}

export async function printEscpos(base64Data, { chunkSize = 100 } = {}) {
  if (!isBluetoothSupported()) {
    throw new Error('Web Bluetooth is not supported in this browser. Try Chrome on Android.');
  }

  // 1) Ask the user to pick their printer
  const device = await navigator.bluetooth.requestDevice({
    filters: [
      { services: [SERVICE_UUID] },
      // Fallback for printers that don't advertise the service
      { namePrefix: 'PT-' },
      { namePrefix: 'XP-' },
      { namePrefix: 'RPP' },
      { namePrefix: 'Printer' },
    ],
    optionalServices: [SERVICE_UUID],
  });

  // 2) Connect and get GATT
  const server = await device.gatt.connect();
  const service = await server.getPrimaryService(SERVICE_UUID);
  const characteristic = await service.getCharacteristic(CHARACTERISTIC_UUID);

  // 3) Decode base64 → Uint8Array
  const binary = atob(base64Data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

  // 4) Write in chunks — most BLE stacks choke on >512 bytes at once
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.slice(i, i + chunkSize);
    await characteristic.writeValue(chunk);
  }

  // 5) Keep connection alive — caller can disconnect later or the OS will
  return device;
}