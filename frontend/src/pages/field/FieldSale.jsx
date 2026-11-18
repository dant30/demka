import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useCart } from '@/store/cart';
import { useCreateSale, useQueueReceipt, useProductLookup } from '@/api/queries';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import PaymentModal from '@/components/pos/PaymentModal';
import ProductGrid from '@/components/pos/ProductGrid';
import CartPanel from '@/components/pos/CartPanel';
import Modal from '@/components/ui/Modal';

export default function FieldSale() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const cart = useCart();
  const createSale = useCreateSale();
  const queueReceipt = useQueueReceipt();
  const lookup = useProductLookup();
  const [search, setSearch] = useState('');
  const [showPayment, setShowPayment] = useState(false);
  const [error, setError] = useState('');
  const mobileCartOpen = searchParams.get('cart') === '1';

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
  const { data: walkInCustomer } = useQuery({
    queryKey: ['walk-in-customer'],
    queryFn: async () => (await api.get(endpoints.customers.walkIn)).data,
    enabled: Boolean(run?.id),
  });

  useEffect(() => {
    if (!run) return;
    cart.setChannel('FIELD');
    cart.setLocation(run.stock_location);
  }, [run?.id, run?.stock_location, cart.setChannel, cart.setLocation]);

  const closeMobileCart = () => {
    const next = new URLSearchParams(searchParams);
    next.delete('cart');
    setSearchParams(next, { replace: true });
  };

  const checkout = () => {
    if (!cart.customerId) {
      setError('Select a customer before charging.');
      closeMobileCart();
      return;
    }
    closeMobileCart();
    setShowPayment(true);
  };

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
    <div className="grid min-w-0 grid-cols-1 gap-4 pb-20 lg:grid-cols-[minmax(0,1fr)_24rem] lg:pb-0">
      <section className="min-w-0 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Field Sale</h1>
          <p className="text-sm text-slate-500">{run.route_name} · {run.stock_location_name}</p>
        </div>
        <Button type="button" size="sm" variant="secondary" onClick={() => navigate('/field')}>
          Back to Runs
        </Button>
      </div>

      <div className="grid min-w-0 grid-cols-2 items-end gap-3">
        <Select
          searchable
          label="Customer"
          value={cart.customerId || ''}
          onChange={(value) => cart.setCustomer(value ? Number(value) : null)}
          options={[
            { value: '', label: 'Select customer...' },
            ...(walkInCustomer ? [{
              value: walkInCustomer.id,
              label: walkInCustomer.name,
              sublabel: walkInCustomer.code,
            }] : []),
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
          aria-label="Scan barcode or enter SKU"
        />
        <Input
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="col-span-2"
        />
      </div>

      {!customers.length && (
        <p className="text-sm text-slate-500">No customers are assigned to this route yet. Choose Walk-in for an unregistered customer.</p>
      )}

      {error && <div className="rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</div>}

      <ProductGrid onAdd={(p) => cart.addItem(p, 1)} search={search} />
      </section>

      <aside className="hidden min-w-0 lg:sticky lg:top-4 lg:block lg:min-h-[20rem] lg:h-[calc(100dvh-var(--topbar-height)-2rem)]">
        <CartPanel
          onCheckout={checkout}
          disabled={createSale.isPending}
          className="rounded-md border border-slate-200 lg:border-l"
        />
      </aside>

      <div className="lg:hidden">
        <Modal open={mobileCartOpen} onClose={closeMobileCart} title="Field Cart" size="lg">
          <div className="h-[62dvh] min-h-64">
            <CartPanel onCheckout={checkout} disabled={createSale.isPending} />
          </div>
        </Modal>
      </div>

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