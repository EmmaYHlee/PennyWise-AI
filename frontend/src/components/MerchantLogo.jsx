import { useState } from 'react';

function initials(name) {
  return name.split(/\s+/).slice(0, 2).map((word) => word[0]).join('').toUpperCase();
}

export default function MerchantLogo({ merchant, logoUrl }) {
  const [logoFailed, setLogoFailed] = useState(!logoUrl);

  return (
    <div className="merchant-logo">
      {!logoFailed && <img src={logoUrl} alt={`${merchant} logo`} onError={() => setLogoFailed(true)} />}
      {logoFailed && <span aria-label={`${merchant} logo unavailable`}>{initials(merchant)}</span>}
    </div>
  );
}
