import { useLocation } from 'react-router-dom';
import { Radar } from 'lucide-react';
import Badge from '../common/Badge';
import { hasBackend } from '../../services/api';

const titles: Record<string, string> = { '/': 'Home', '/dashboard': 'Dashboard', '/history': 'History', '/reports': 'Reports', '/settings': 'Settings' };

export default function Topbar() {
  const { pathname } = useLocation();
  const title = pathname.startsWith('/scan/') ? 'Scan results' : titles[pathname] ?? 'Not found';
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-edge bg-ink/80 px-4 backdrop-blur sm:px-8">
      <div className="flex items-center gap-2 lg:hidden"><Radar className="h-5 w-5 text-brand" /><span className="font-display font-bold">DeadLink Hunter</span></div>
      <h2 className="hidden font-display text-lg font-semibold lg:block">{title}</h2>
      <Badge tone={hasBackend ? 'ok' : 'warn'} pulse>{hasBackend ? 'Backend configured' : 'Demo mode · mock data'}</Badge>
    </header>
  );
}
