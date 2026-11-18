import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import { formatKes } from '@/utils/money';
import { useMpesaStkPush } from '@/api/queries';

const METHODS = [
  { code: 'CASH', label: 'Cash' },
  { code: 'MPESA', label: 'M-Pesa' },
  { code: 'CHEQUE', label: 'Cheque' },
  { code: 'BANK_TRANSFER', label: 'Bank Transfer' },
  { code: 'CREDIT', label: 'Credit (on account)' },
];

export default function PaymentModal({
  open, onClose, total, customerId, onConfirm,
}) {
  const [method, setMethod] = useState('CASH');
  const [amount, setAmount] = useState(Number(total).toFixed(2));
  const [reference, setReference] = useState('');
  const [mpesaPhone, setMpesaPhone] = useState('');
  const stkPush = useMpesaStkPush();

  const amountNum = Number(amount) || 0;
  const remaining = total - amountNum;

  const handleConfirm = () => {
    onConfirm({
      method,
      amount: amountNum,
      reference,
      mpesa_phone: mpesaPhone,
      mpesa_transaction_id: reference,
    });
  };

  const handleStkPush = async () => {
    if (!customerId) return alert('Select a customer first.');
    try {
      await stkPush.mutateAsync({
        customer: customerId,
        phone: mpesaPhone || reference,
        amount: amountNum,
        account_reference: `POS-${Date.now()}`,
      });
      alert('STK push sent. Ask the customer to enter their M-Pesa PIN.');
    } catch (e) {
      alert('M-Pesa request failed.');
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Complete Payment" size="md"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={handleConfirm} disabled={amountNum <= 0}>
            Confirm {formatKes(amountNum)}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="rounded-xl bg-slate-50 p-4">
          <div className="text-sm text-slate-500">Total Due</div>
          <div className="text-3xl font-bold text-slate-900">{formatKes(total)}</div>
        </div>

        <Select label="Payment Method" value={method} onChange={(e) => setMethod(e.target.value)}>
          {METHODS.map((m) => (
            <option key={m.code} value={m.code}>{m.label}</option>
          ))}
        </Select>

        <Input
          label="Amount Received"
          type="number"
          step="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />

        {method === 'MPESA' && (
          <>
            <Input
              label="M-Pesa Phone"
              placeholder="07XXXXXXXX"
              value={mpesaPhone}
              onChange={(e) => setMpesaPhone(e.target.value)}
            />
            <Button variant="secondary" onClick={handleStkPush} loading={stkPush.isPending}>
              Send STK Push
            </Button>
            <Input
              label="M-Pesa Receipt (after payment)"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
            />
          </>
        )}

        {(method === 'CHEQUE' || method === 'BANK_TRANSFER') && (
          <Input
            label="Reference Number"
            value={reference}
            onChange={(e) => setReference(e.target.value)}
          />
        )}

        {remaining > 0 && method !== 'CREDIT' && (
          <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
            <strong>{formatKes(remaining)}</strong> remains — will be added to the
            customer's credit.
          </div>
        )}
      </div>
    </Modal>
  );
}