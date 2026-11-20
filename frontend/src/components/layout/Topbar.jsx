import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useCart } from "@/store/cart";
import { useTodayFieldRuns } from "@/hooks/useTodayFieldRuns";

const PAGE_TITLES = {
  "/": "Dashboard",
  "/profile": "My Profile",
  "/pos": "Shop POS",
  "/field": "Field Sales",
  "/sales": "Sales",
  "/inventory": "Inventory",
  "/customers": "Customers",
  "/suppliers": "Suppliers",
  "/purchasing": "Purchasing",
  "/routes": "Routes",
  "/payments": "Payments",
  "/expenses": "Expenses",
  "/preorders": "Preorders",
  "/reports": "Reports",
};

function titleFor(pathname) {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  // Match the top-level segment for deep pages like /sales/123
  const seg = "/" + pathname.split("/")[1];
  return PAGE_TITLES[seg] || "DEMKA";
}

export default function Topbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const cartCount = useCart((state) => state.itemCount());
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);
  const isFieldAgent = user?.role === 'FIELD_AGENT';
  const { activeRuns } = useTodayFieldRuns(user, { enabled: isFieldAgent });
  const activeRun = activeRuns[0];
  const saleDestination = isFieldAgent
    ? activeRun ? `/field/sale/${activeRun.id}` : '/field'
    : '/pos';
  const cartDestination = isFieldAgent && activeRun
    ? `${saleDestination}?cart=1`
    : isFieldAgent ? '/field' : '/pos/cart';

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event) => {
      if (!menuRef.current?.contains(event.target)) setOpen(false);
    };
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const initials = (user?.full_name || user?.username || "?").trim()[0].toUpperCase();

  return (
    <header
      className="
        sticky top-0 z-30
        bg-white/95 backdrop-blur-sm
        border-b border-slate-200 shadow-sm
        flex items-center justify-between
        px-4 md:px-6
      "
      style={{ height: "var(--topbar-height)" }}
    >
      {/* Left: brand (mobile) / page title (desktop) */}
      <div className="flex items-center gap-3 min-w-0">
        <Link to="/" className="md:hidden font-bold text-brand-700 tracking-tight">
          DEMKA
        </Link>
        <h1 className="hidden md:block text-base font-semibold text-slate-900 truncate">
          {titleFor(location.pathname)}
        </h1>
      </div>

      {/* Right: quick action + user menu */}
      <div className="flex items-center gap-2">
        <Link
          to={cartDestination}
          className="md:hidden relative inline-flex h-10 w-10 items-center justify-center rounded-full text-slate-700 hover:bg-slate-100"
          aria-label={isFieldAgent ? (activeRun ? 'Open field cart' : 'Open Field Sales') : `Cart with ${cartCount} item${cartCount === 1 ? '' : 's'}`}
          title={isFieldAgent ? 'Open field cart' : 'Open cart'}
        >
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
            <path d="M3 3h2l2.4 11.2a2 2 0 001.9 1.5h7.9a2 2 0 001.9-1.4L21 7H6" />
            <circle cx="10" cy="20" r="1" fill="currentColor" stroke="none" />
            <circle cx="18" cy="20" r="1" fill="currentColor" stroke="none" />
          </svg>
          {cartCount > 0 && (
            <span className="absolute right-0 top-0 min-w-5 rounded-full bg-brand-600 px-1 text-center text-[10px] leading-5 text-white">
              {cartCount}
            </span>
          )}
        </Link>
        <Link
          to={saleDestination}
          className="hidden md:inline-flex btn-primary btn-sm"
        >
          {isFieldAgent ? (activeRun ? 'Field Sale' : 'Field Sales') : '+ New Sale'}
        </Link>

        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            className="flex items-center gap-2 rounded-lg pl-1 pr-2 py-1 hover:bg-slate-100 transition-colors"
            aria-haspopup="menu"
            aria-expanded={open}
          >
            <span className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm font-semibold flex-shrink-0">
              {initials}
            </span>
            <span className="hidden sm:flex flex-col items-start leading-tight min-w-0">
              <span className="text-sm font-medium text-slate-900 truncate max-w-[10rem]">
                {user?.full_name || user?.username}
              </span>
              <span className="text-[11px] text-slate-500 uppercase tracking-wide">
                {user?.role}
              </span>
            </span>
          </button>

          {open && (
            <div
              role="menu"
              className="absolute right-0 top-full z-40 mt-1 w-52 rounded-lg border border-slate-200 bg-white py-1 shadow-lg animate-scale-in"
            >
              <div className="px-4 py-2 border-b border-slate-100 sm:hidden">
                <div className="text-sm font-medium truncate">{user?.full_name || user?.username}</div>
                <div className="text-xs text-slate-500">{user?.phone}</div>
              </div>
              <Link
                to="/profile"
                onClick={() => setOpen(false)}
                className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                Profile
              </Link>
              <Link
                to="/admin/printers"
                onClick={() => setOpen(false)}
                className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                Printers
              </Link>
              <div className="h-px bg-slate-100 my-1" />
              <button
                type="button"
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}