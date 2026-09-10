import ReactMarkdown from 'react-markdown';
import TransactionItem from './TransactionItem';

export default function Message({ message }) {
  const isUser = message.role === 'user';

  return (
    <article className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
      {!isUser && <div className="assistant-avatar" aria-hidden="true">P</div>}

      <div className="message-content">
        {!isUser && <span className="message-author">PennyWise</span>}

        <div className="message-text">
          <ReactMarkdown>{message.text}</ReactMarkdown>
        </div>

        {message.type === 'transaction_list' && (
          <div className="transaction-list">
            {message.data.transactions.map((transaction) => (
              <TransactionItem key={`${transaction.merchant}-${transaction.date || transaction.detail}`} transaction={transaction} />
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
