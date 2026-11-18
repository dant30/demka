import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import BottomBar from "./BottomBar";
import MobileDrawer from "./MobileDrawer";

/**
 * Top-level application shell.
 *
 * Desktop:  [Sidebar] | [Topbar]
 *                      [Content]
 *
 * Mobile:   [Topbar]
 *           [Content]
 *           [BottomBar]
 *           [Drawer — on "More" tap]
 */
export default function AppShell() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="h-[100dvh] flex overflow-hidden bg-slate-50">
      {/* Sidebar — desktop only */}
      <Sidebar />

      {/* Main column — topbar + content */}
      <div className="flex-1 flex flex-col min-h-0 min-w-0">
        <Topbar />

        <main className="flex-1 overflow-y-auto has-bottombar">
          <div className="app-content px-4 py-4 md:px-6 md:py-6">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile-only fixed bottom navigation */}
      <BottomBar onOpenMore={() => setDrawerOpen(true)} />

      {/* Mobile-only "More" bottom sheet */}
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  );
}