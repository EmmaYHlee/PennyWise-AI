import { useState } from 'react';

export default function NamePrompt({ onContinue }) {
  const [name, setName] = useState('');
  const submit = (event) => {
    event.preventDefault();
    if (name.trim()) onContinue(name);
  };

  return (
    <section className="name-prompt">
      <div className="onboarding-logo" aria-hidden="true">P</div>
      <p className="eyebrow">WELCOME TO PENNYWISE</p>
      <h2>Let’s make money feel simpler.</h2>
      <p>Before we begin, what should I call you?</p>
      <form onSubmit={submit}>
        <label htmlFor="name">Your first name</label>
        <input id="name" autoFocus autoComplete="given-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Emma" maxLength="40" />
        <button className="primary-button" type="submit" disabled={!name.trim()}>Continue <span aria-hidden="true">→</span></button>
      </form>
      <small>We use your name only to personalize this conversation.</small>
    </section>
  );
}
