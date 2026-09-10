import MerchantLogo from './MerchantLogo';

export default function TransactionItem({ transaction }) {
  const detail = transaction.detail || [transaction.subcategory, transaction.date].filter(Boolean).join(' · ');
  const amount = typeof transaction.amount === 'number'
    ? `${transaction.transaction_type === 'income' ? '+' : '−'}$${Math.abs(transaction.amount).toFixed(2)}`
    : transaction.amount;

  return (
    <div className="transaction-item">
      <MerchantLogo merchant={transaction.merchant} logoUrl={transaction.logo_url} />
      <div className="transaction-merchant"><strong>{transaction.merchant}</strong><span>{detail}</span></div>
      <strong className="transaction-amount">{amount}</strong>
    </div>
  );
}
