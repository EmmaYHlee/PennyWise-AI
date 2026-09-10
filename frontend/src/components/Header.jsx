export default function Header({ onChangeName }) {
  return (
    <header className="app-header">
      <button className="back-button" type="button" aria-label="Go back">‹</button>
      <div><strong>PennyWise <i>AI</i></strong><span>Your spending assistant</span></div>
      <button className="menu-button" type="button" onClick={onChangeName} aria-label="Change your name">•••</button>
    </header>
  );
}
