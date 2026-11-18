import { useCart } from '@/store/cart';
import { formatKes } from '@/utils/money';

export default function CartPanel({ onCheckout, disabled, className = '' }) {
  const {
    items, updateQuantity, removeItem, subtotal, itemCount, clear,
  } = useCart();

  const total = subtotal();
  const tax = 0; // computed server-side at preview

  return (
    <div className={`flex h-full min-h-0 flex-col bg-white border-l border-slate-200 ${className}`.trim()}>
      <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <div>
          <div className="font-semibold">Cart</div>
          <div className="text-xs text-slate-500">{itemCount()} items</div>
        </div>
        {items.length > 0 && (
          <button onClick={clear} className="text-xs text-red-600 hover:underline">
            Clear
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2">
        {items.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            Scan or tap a product to add it.
          </div>
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <div key={item.product.id} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="font-medium text-sm truncate">{item.product.name}</div>
                    <div className="text-xs text-slate-500">{formatKes(item.unitPrice)}</div>
                  </div>
                  <button
                    onClick={() => removeItem(item.product.id)}
                    className="text-red-500 text-sm"
                  >
                    ✕
                  </button>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                      className="w-8 h-8 rounded-lg border border-slate-300 font-semibold"
                    >−</button>
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) =>
                        updateQuantity(item.product.id, Number(e.target.value) || 0)
                      }
                      className="w-14 text-center rounded-lg border border-slate-300 py-1"
                    />
                    <button
                      onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                      className="w-8 h-8 rounded-lg border border-slate-300 font-semibold"
                    >+</button>
                  </div>
                  <div className="font-semibold text-sm">{formatKes(item.lineTotal)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-slate-200 p-4 space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-slate-600">Subtotal</span>
          <span className="font-medium">{formatKes(total)}</span>
        </div>
        <div className="flex justify-between text-lg font-semibold">
          <span>Total (excl. tax)</span>
          <span>{formatKes(total)}</span>
        </div>
        <button
          onClick={onCheckout}
          disabled={disabled || items.length === 0}
          className="btn-primary btn-lg w-full"
        >
          Charge {formatKes(total)}
        </button>
      </div>
    </div>
  );
}