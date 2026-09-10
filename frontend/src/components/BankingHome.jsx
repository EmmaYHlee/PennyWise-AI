import { useEffect, useState } from 'react';
import TransactionItem from './TransactionItem';
import { getDashboard } from '../services/api';

export default function BankingHome({ name, onOpenChat, onChangeName }) {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState('');

  const loadDashboard = () => {
    setError('');
    getDashboard().then(setDashboard).catch(() => {
      setError('PennyWise could not reach the banking service. Start the backend to load account data.');
    });
  };

  useEffect(() => { loadDashboard(); }, []);

  if (!dashboard) {
    return <main className="banking-app"><header className="banking-header"><button className="wordmark" type="button"><span>P</span> PennyWise</button></header><section className="dashboard-content dashboard-state"><p className="eyebrow">ACCOUNT OVERVIEW</p><h1>{error ? 'Connection needed' : 'Loading your account…'}</h1>{error && <><p>{error}</p><button className="primary-button" type="button" onClick={loadDashboard}>Try again <span>→</span></button></>}</section></main>;
  }

  const { insight, recent_transactions: recentTransactions } = dashboard;

  return (
    <main className="banking-app">
      <header className="banking-header">
        <button className="wordmark" type="button" aria-label="PennyWise home"><span>P</span> PennyWise</button>
        <nav aria-label="Main navigation"><button className="nav-active" type="button">Overview</button><button type="button">Move money</button><button type="button">Profile</button></nav>
        <button className="profile-button" type="button" onClick={onChangeName} aria-label="Change profile name">{name.slice(0, 1).toUpperCase()}</button>
      </header>

      <section className="dashboard-content">
        <div className="welcome-row"><div><p className="eyebrow">ACCOUNT OVERVIEW</p><h1>Hello, {name}.</h1></div></div>

        <section className="dashboard-grid">
          <article className="insight-card"><span className="insight-icon">✦</span><p>PENNYWISE AI</p><h2>{insight}</h2><button type="button" onClick={onOpenChat}>Ask PennyWise <span>→</span></button></article>
        </section>

        <section className="activity-section"><div className="section-heading"><div><p className="eyebrow">ACTIVITY</p><h2>Recent transactions</h2></div><button type="button">View all</button></div><div className="activity-list">{recentTransactions.map((transaction) => <TransactionItem key={`${transaction.merchant}-${transaction.date}`} transaction={transaction} />)}</div></section>
      </section>
      <button className="assistant-launcher" type="button" onClick={onOpenChat} aria-label="Open PennyWise AI"><span className="launcher-mark">P</span><span><b>Ask PennyWise</b><small>Your spending assistant</small></span><i>↗</i></button>
    </main>
  );
}
