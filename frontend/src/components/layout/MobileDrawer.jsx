import { useEffect } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

/**
 * Full navigation menu as a bottom sheet, triggered by the "More" button
 * in the bottom bar. Grouped identically to the desktop sidebar.
 */
const NAV_GROUPS = [
  {
    title: "Operations",
    items: [
      { to: "/",            label: "Dashboard",  icon: "📊", bossOnly: true,  end: true },
      { to: "/pos",         label: "Shop POS",   icon: "🛒", shopOnly: true },
      { to: "/field",       label: "Field Sales", icon: "🚐", fieldOnly: true },
      { to: "/sales",       label: "Sales",      icon: "🧾" },
      { to: "/preorders",   label: "Preorders",  icon: "📝" },
    ],
  },
  {
    title: "Inventory",
    items: [
      { to: "/inventory",   label: "Products",   icon: "📦" },
      { to: "/purchasing",  label: "Purchasing", icon: "📥", bossOnly: true },
      { to: "/suppliers",   label: "Suppliers",  icon: "🚚", bossOnly: true },
    ],
  },
  {
    title: "Customers",
    items: [
      { to: "/customers",   label: "Customers",  icon: "👥" },
      { to: "/routes",      label: "Routes",     icon: "🗺️" },
    ],
  },
  {
    title: "Finance",
    items: [
      { to: "/payments",    label: "Payments",   icon: "💳" },
      { to: "/expenses",    label: "Expenses",   icon: "💸" },
      { to: "/reports",     label: "Reports",    icon: "📈", bossOnly: true },
    ],
  },
  {
    title: "Admin",
    items: [
      { to: "/admin/etims",    label: "eTIMS",    icon: "🏛️", bossOnly: true },
      { to: "/admin/printers", label: "Printers", icon: "🖨️", bossOnly: true },
      { to: "/admin/users",    label: "Users",    icon: "🔧", bossOnly: true },
    ],
  },
];

export default function MobileDrawer({ open, onClose }) {
  const { user } = useAuth();
  const role = user?.role;
  const isBoss = role === "BOSS" || role === "ADMIN";
  const isField = role === "FIELD_AGENT";

  // Lock body scroll when the drawer is open.
  useEffect(() => {
    if (!open) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = original;
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div className="sheet-backdrop animate-fade-in" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="All navigation"
        className="sheet-panel animate-slide-up"
      >
        {/* Header with drag handle indicator */}
        <div className="flex justify-center pt-2 pb-1">
          <div className="w-10 h-1 rounded-full bg-slate-300" />
        </div>
        <div className="flex items-center justify-between px-4 pb-2 border-b border-slate-100">
          <span className="font-semibold text-slate-900">All navigation</span>
          <button
            onClick={onClose}
            className="btn-icon"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto px-3 py-2" style={{ maxHeight: "calc(85vh - 4rem)" }}>
          {NAV_GROUPS.map((group) => {
            const visible = group.items.filter((item) => {
              if (item.bossOnly && !isBoss) return false;
              if (item.fieldOnly && !isField && !isBoss) return false;
              if (item.shopOnly && isField) return false;
              return true;
            });
            if (visible.length === 0) return null;

            return (
              <section key={group.title} className="mb-3">
                <h3 className="px-2 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  {group.title}
                </h3>
                <div className="grid grid-cols-1 gap-1">
                  {visible.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.end}
                      onClick={onClose}
                      className={({ isActive }) =>
                        `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-brand-50 text-brand-700"
                            : "text-slate-700 hover:bg-slate-100"
                        }`
                      }
                    >
                      <span className="text-lg leading-none w-5 text-center flex-shrink-0">
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </NavLink>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </>
  );
}