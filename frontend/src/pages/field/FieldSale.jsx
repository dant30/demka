import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useCart } from '@/store/cart';
import { useCreateSale, useQueueReceipt, useProductLookup } from '@/api/queries';
import { formatKes } from '@/utils/money';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import PaymentModal from '@/components/pos/PaymentModal';
import ProductGrid from '@/components/pos/ProductGrid';

export default function FieldSale() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const cart = useCart();
  const createSale = useCreateSale();
  const queueReceipt = useQueueReceipt();
  const lookup = useProductLookup();
  const [search, setSearch] = useState('');
  const [showPayment, setShowPayment] = useState(false);
  const [error, setError] = useState('');

  // Load the run + its stock location
  const { data: run } = useQuery({
    queryKey: ['run', runId],
    queryFn: async () => (await api.get(endpoints.routes.runDetail(runId))).data,
  });

  // Load customers on this run's route
  const { data: customersData } = useQuery({
    queryKey: ['route-customers', run?.route],
    queryFn: async () => {
      const { data } = await api.get(endpoints.customers.list, {
        params: { route: run.route, page_size: 200 },
      });
      return data;
    },
    enabled: !!run?.route,
  });

  const customers = customersData?.results || customersData || [];

  // Auto-set the location + channel once the run loads
  if (run && cart.channel !== 'FIELD') {
    cart.setChannel('FIELD');
    cart.setLocation(run.stock_location);
  }

  const handleBarcode = async (e) => {
    if (e.key !== 'Enter') return;
    const value = e.target.value.trim();
    if (!value) return;
    try {
      const product = await lookup.mutateAsync(
        value.length > 8 ? { barcode: value } : { sku: value }
      );
      cart.addItem(product, 1);
      e.target.value = '';
    } catch {
      setError(`No product found for "${value}"`);
    }
  };

  const handleConfirm = async (payment) => {
    setError('');
    try {
      const sale = await createSale.mutateAsync({
        channel: 'FIELD',
        sale_type: 'STANDARD',
        customer: cart.customerId,
        location: run.stock_location,
        route: run.route,
        items: cart.items.map((i) => ({
          product: i.product.id,
          quantity: i.quantity,
          unit_price: i.unitPrice,
        })),
        amount_paid: payment.amount,
        payment_method: payment.method,
        payment_reference: payment.reference,
        confirm: true,
      });
      setShowPayment(false);

      // Queue receipt, then offer Bluetooth printing
      const job = await queueReceipt.mutateAsync(sale.id);
      cart.clear();
      navigate(`/field/sale-receipt/${sale.id}?receiptJob=${job.id}`);
    } catch (err) {
      setError(extractError(err, 'Sale failed.'));
    }
  };

  if (!run) return <div>Loading...</div>;

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Field Sale</h1>
          <p className="text-sm text-slate-500">{run.route_name} · {run.stock_location_name}</p>
        </div>
        <button onClick={() => navigate('/field')} className="text-sm text-slate-500 hover:underline">
          ← Back
        </button>
      </div>

      <Select
        searchable
        label="Customer"
        value={cart.customerId || ''}
        onChange={(value) => cart.setCustomer(value ? Number(value) : null)}
        options={[
          { value: '', label: 'Select customer...' },
          ...customers.map((customer) => ({
            value: customer.id,
            label: customer.name,
            sublabel: customer.code,
          })),
        ]}
      />

      <Input
        placeholder="Scan barcode or type SKU + Enter"
        onKeyDown={handleBarcode}
        autoFocus
      />
      <Input
        placeholder="Search products..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {error && <div className="rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</div>}

      <ProductGrid onAdd={(p) => cart.addItem(p, 1)} search={search} />

      {cart.items.length > 0 && (
        <div className="card sticky bottom-4">
          <div className="space-y-2 mb-3 max-h-64 overflow-y-auto">
            {cart.items.map((it) => (
              <div key={it.product.id} className="flex justify-between text-sm border-b border-slate-100 pb-1">
                <div>
                  {it.product.name} × {it.quantity}
                </div>
                <div>{formatKes(it.lineTotal)}</div>
              </div>
            ))}
          </div>
          <div className="flex justify-between items-center text-lg font-semibold pt-2 border-t">
            <span>Total</span>
            <span>{formatKes(cart.subtotal())}</span>
          </div>
          <button
            onClick={() => cart.customerId ? setShowPayment(true) : setError('Select a customer.')}
            className="btn-primary w-full mt-3"
            disabled={createSale.isPending}
          >
            Charge
          </button>
        </div>
      )}

      <PaymentModal
        open={showPayment}
        onClose={() => setShowPayment(false)}
        total={cart.subtotal() * 1.16}
        customerId={cart.customerId}
        onConfirm={handleConfirm}
      />
    </div>
  );
}