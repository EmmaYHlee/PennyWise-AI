const suggestions = [
  ['↗', 'Top spending categories', 'Where did most of my money go?'],
  ['⌁', 'Dining spending', 'How much did I spend on dining?'],
  ['☕', 'Coffee shop visits', 'Show me all coffee shop visits with their logos'],
  ['◌', 'Show subscriptions', 'What subscriptions do I have?'],
  ['◎', 'Top merchants', 'Which merchants do I spend the most at?'],
  ['✦', 'Unusual spending', 'Are there any unusual transactions?'],
];

export default function SuggestedQuestions({ onSelect, disabled }) {
  return <section className="suggestions" aria-label="Suggested questions">
    <p>Here are a few ways to get started</p>
    {suggestions.map(([icon, label, question]) => <button type="button" key={label} onClick={() => onSelect(question)} disabled={disabled}><b aria-hidden="true">{icon}</b><span>{label}</span><i aria-hidden="true">›</i></button>)}
  </section>;
}
