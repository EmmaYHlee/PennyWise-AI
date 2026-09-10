import { useEffect, useRef, useState } from 'react';
import { sendChatMessage } from '../services/api';
import Message from './Message';
import SuggestedQuestions from './SuggestedQuestions';
import TypingIndicator from './TypingIndicator';

export default function Chat({ name, onClose }) {
  const [messages, setMessages] = useState([{ id: 'welcome', role: 'assistant', text: `Hello ${name} — I’m PennyWise, your spending assistant. I can help you understand where your money goes, spot trends, and keep an eye on recurring charges.` }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, error]);

  const sendMessage = async (question) => {
    const text = question.trim();
    if (!text || loading) return;
    setInput('');
    setError('');
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'user', text }]);
    setLoading(true);
    try {
      const history = messages
        .filter((message) => message.role === 'user' || message.role === 'assistant')
        .map((message) => ({
          role: message.role === 'assistant' ? 'model' : 'user',
          content: message.text,
        }));

      const response = await sendChatMessage(text, history);
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'assistant', text: response.response, type: response.type, data: response.data }]);
    } catch {
      setError('Sorry, I couldn’t analyze your transactions right now. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="chat-overlay" role="dialog" aria-modal="true" aria-label="PennyWise chat">
      <button className="chat-backdrop" type="button" onClick={onClose} aria-label="Close PennyWise chat" />
      <div className="chat-panel">
      <header className="chat-panel-header"><div className="panel-brand"><b>P</b><span><strong>PennyWise <i>AI</i></strong><small>Ready to help with your money</small></span></div><button type="button" className="close-chat" onClick={onClose} aria-label="Close chat">×</button></header>
      <div className="chat" aria-label="PennyWise messages">
      <div className="chat-scroll">
        <div className="chat-date">TODAY</div>
        {messages.map((message) => <Message key={message.id} message={message} />)}
        {messages.length === 1 && <SuggestedQuestions onSelect={sendMessage} disabled={loading} />}
        {loading && <TypingIndicator />}
        {error && <div className="error-message" role="alert"><span>{error}</span><button type="button" onClick={() => sendMessage(messages.at(-1)?.text || '')}>Retry</button></div>}
        <div ref={endRef} />
      </div>
      <form className="composer" onSubmit={(event) => { event.preventDefault(); sendMessage(input); }}>
        <input aria-label="Ask PennyWise" value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask PennyWise..." disabled={loading} />
        <button type="submit" disabled={!input.trim() || loading} aria-label="Send message">↑</button>
      </form>
      </div>
      </div>
    </section>
  );
}
