import { useNavigate } from 'react-router-dom';
import { useCart } from '@/store/cart';
import CartPanel from '@/components/pos/CartPanel';

export default function POSCart() {
  const navigate = useNavigate();
  const customerId = useCart((state) => state.customerId);
  const locationId = useCart((state) => state.locationId);

  const handleCheckout = () => {
    navigate('/pos', { state: { openPayment: true } });
  };

  return (
    <div className="mx-auto h-[calc(100dvh-11rem)] w-full max-w-xl md:h-[calc(100dvh-7rem)]">
      <CartPanel
        onCheckout={handleCheckout}
        disabled={!customerId || !locationId}
      />
    </div>
  );
}
