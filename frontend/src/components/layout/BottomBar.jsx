import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useCart } from "@/store/cart";
import { useAuth } from "@/hooks/useAuth";
import { useTodayFieldRuns } from "@/hooks/useTodayFieldRuns";

/**
 * Role-aware primary navigation items for the mobile bottom bar.
 * These four slots are the highest-frequency destinations for each role.
 * Everything else lives behind the "More" button.
 */
function primaryItemsFor(role) {
  if (role === "FIELD_AGENT") {
    return [
      { to: "/field",       label: "Field",     icon: "🚐", match: "/field" },
      { to: "/sales",       label: "Sales",     icon: "🧾", match: "/sales" },
      { to: "/customers",   label: "Customers", icon: "👥", match: "/customers" },
    ];
  }
  if (role === "SALES_HELPER") {
    return [
      { to: "/customers",   label: "Customers", icon: "👥", match: "/customers" },
      { to: "/sales",       label: "Sales",     icon: "🧾", match: "/sales" },
      { to: "/inventory",   label: "Stock",     icon: "📦", match: "/inventory" },
    ];
  }
  // BOSS / ADMIN
  return [
    { to: "/",            label: "Home",      icon: "📊", match: "/", end: true },
    { to: "/inventory",   label: "Products",  icon: "📦", match: "/inventory" },
    { to: "/sales",       label: "Sales",     icon: "🧾", match: "/sales" },
  ];
}

export default function BottomBar({ onOpenMore }) {
  const { user } = useAuth();
  const clearCart = useCart((state) => state.clear);
  const location = useLocation();
  const navigate = useNavigate();
  const items = primaryItemsFor(user?.role);
  const isFieldAgent = user?.role === 'FIELD_AGENT';
  const { activeRuns } = useTodayFieldRuns(user, { enabled: isFieldAgent });
  const activeRun = activeRuns[0];

  // A slot is active if pathname starts with its `match` (except Home uses end-match).
  const isActive = (item) => {
    if (item.end) return location.pathname === item.to;
    return (
      location.pathname === item.match ||
      location.pathname.startsWith(item.match + "/")
    );
  };

  return (
    <nav
      className="md:hidden fixed inset-x-0 bottom-0 z-40 bg-white border-t border-slate-200"
      style={{ paddingBottom: "var(--safe-bottom)" }}
      aria-label="Primary navigation"
    >
      <div
        className="flex items-stretch"
        style={{ height: "var(--bottombar-height)" }}
      >
        {items.slice(0, 2).map((item) => {
          const active = isActive(item);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={`flex-1 flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition-colors ${
                active ? "text-brand-600" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <span className={`text-xl leading-none ${active ? "scale-110" : ""} transition-transform`}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </NavLink>
          );
        })}

        <button
          onClick={() => {
            if (isFieldAgent) {
              navigate(activeRun ? `/field/sale/${activeRun.id}` : '/field');
              return;
            }
            clearCart();
            navigate("/pos");
          }}
          className="relative flex-1 flex items-center justify-center text-[11px] font-semibold text-brand-700"
          aria-label={isFieldAgent ? (activeRun ? 'Open field sale' : 'Open Field Sales') : 'Start new sale'}
        >
          <span className="absolute -top-5 flex h-14 w-14 items-center justify-center rounded-full border-4 border-white bg-brand-600 text-[30px] leading-none text-white shadow-[0_8px_20px_rgba(37,99,235,0.35)] transition-transform active:scale-95">
            +
          </span>
          <span className="absolute bottom-1 text-[10px]">{isFieldAgent ? 'Field Sale' : 'New Sale'}</span>
        </button>

        {items.slice(2).map((item) => {
          const active = isActive(item);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={`flex-1 flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition-colors ${
                active ? "text-brand-600" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <span className={`text-xl leading-none ${active ? "scale-110" : ""} transition-transform`}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </NavLink>
          );
        })}

        {/* "More" opens the drawer */}
        <button
          onClick={onOpenMore}
          className="flex-1 flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium text-slate-500 hover:text-slate-700 transition-colors"
          aria-label="More navigation"
        >
          <span className="text-xl leading-none">☰</span>
          <span>More</span>
        </button>
      </div>
    </nav>
  );
}