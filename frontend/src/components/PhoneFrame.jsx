export default function PhoneFrame({ children }) {
  return (
    <div className="phone" aria-label="PennyWise mobile banking application">
      <div className="phone-notch" aria-hidden="true" />
      <div className="phone-screen">
        <div className="status-bar" aria-hidden="true"><span>9:41</span><span>●●● ◔</span></div>
        {children}
      </div>
      <div className="home-indicator" aria-hidden="true" />
    </div>
  );
}
