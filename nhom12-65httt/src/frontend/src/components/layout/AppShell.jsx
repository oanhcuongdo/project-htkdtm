import { useState } from 'react';
import { ChatAssistantDrawer } from '../chat/ChatAssistantDrawer';
import { Footer } from './Footer';
import { Navbar } from './Navbar';

export function AppShell({ children }) {
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col bg-[#F0FDFA]">
      <Navbar onOpenChat={() => setChatOpen((prev) => !prev)} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">{children}</main>
      <Footer />
      <ChatAssistantDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}
