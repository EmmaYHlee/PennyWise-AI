import { useState } from 'react';
import BankingHome from './components/BankingHome';
import Chat from './components/Chat';
import NamePrompt from './components/NamePrompt';
import PhoneFrame from './components/PhoneFrame';

export default function App() {
  const [name, setName] = useState('');
  const [chatOpen, setChatOpen] = useState(false);

  const saveName = (nextName) => {
    const cleanName = nextName.trim();
    setName(cleanName);
  };

  const resetName = () => {
    setName('');
  };

  return (
    <main className="app-shell">
      <aside className="brand-intro" aria-hidden="true">
        <div className="brand-mark">P</div>
        <p className="eyebrow">PENNYWISE AI</p>
        <h1>Money clarity, whenever you need it.</h1>
        <p className="brand-copy">A conversational guide that makes your everyday banking feel more human.</p>
        <p className="trust-note"><span>✦</span> Demo experience — sample account data only</p>
      </aside>
      <PhoneFrame>
        {!name ? <NamePrompt onContinue={saveName} /> : <BankingHome name={name} onOpenChat={() => setChatOpen(true)} onChangeName={resetName} />}
        {name && chatOpen && <Chat name={name} onClose={() => setChatOpen(false)} />}
      </PhoneFrame>
    </main>
  );
}
