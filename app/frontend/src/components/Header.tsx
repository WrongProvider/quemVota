import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";

export default function Header() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "unset";
    return () => { document.body.style.overflow = "unset"; };
  }, [open]);

  const navLinks = [
    { name: "Home", href: "/" },
    { name: "Parlamentares", href: "/politicos" },
    { name: "Metodologia", href: "/metodologia" },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

        .header-root {
          font-family: 'DM Sans', sans-serif;
        }

        /* NAV */
        .nav-bar {
          position: fixed;
          top: 0; left: 0;
          z-index: 50;
          width: 100%;
          transition: background 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease;
        }
        .nav-bar.scrolled {
          background: rgba(255,255,255,0.92);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border-bottom: 1px solid rgba(0,0,0,0.07);
          box-shadow: 0 1px 24px rgba(0,0,0,0.05);
        }

        .nav-inner {
          max-width: 1100px;
          margin: 0 auto;
          padding: 0 24px;
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        /* LOGO */
        .logo-link {
          display: flex;
          align-items: center;
          gap: 8px;
          text-decoration: none;
        }
        .logo-mark {
          width: 28px;
          height: 28px;
          background: #1a1a1a;
          border-radius: 7px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: background 0.2s;
        }
        .logo-mark svg {
          width: 14px;
          height: 14px;
        }
        .logo-text {
          font-family: 'DM Mono', monospace;
          font-size: 15px;
          font-weight: 500;
          color: #1a1a1a;
          letter-spacing: -0.3px;
        }
        .logo-text span {
          color: #2563eb;
        }
        .logo-link:hover .logo-mark {
          background: #2563eb;
        }

        /* DESKTOP LINKS */
        .desktop-links {
          display: none;
          align-items: center;
          gap: 2px;
        }
        @media (min-width: 768px) {
          .desktop-links { display: flex; }
        }

        .nav-link {
          position: relative;
          padding: 6px 14px;
          font-size: 14px;
          font-weight: 400;
          color: #52525b;
          text-decoration: none;
          border-radius: 8px;
          transition: color 0.2s, background 0.2s;
          letter-spacing: 0.01em;
        }
        .nav-link:hover {
          color: #1a1a1a;
          background: rgba(0,0,0,0.04);
        }
        .nav-link.active {
          color: #1a1a1a;
          font-weight: 500;
        }
        .nav-link.active::after {
          content: '';
          position: absolute;
          bottom: -1px;
          left: 14px;
          right: 14px;
          height: 2px;
          background: #2563eb;
          border-radius: 2px;
        }

        .cta-btn {
          margin-left: 16px;
          padding: 8px 18px;
          font-size: 13.5px;
          font-weight: 500;
          color: #fff;
          background: #1a1a1a;
          border: none;
          border-radius: 8px;
          text-decoration: none;
          cursor: pointer;
          transition: background 0.2s, transform 0.15s;
          letter-spacing: 0.01em;
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }
        .cta-btn:hover {
          background: #2563eb;
          transform: translateY(-1px);
        }
        .cta-btn:active {
          transform: translateY(0);
        }
        .cta-btn svg {
          width: 13px;
          height: 13px;
          opacity: 0.8;
        }

        /* HAMBURGER */
        .hamburger-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 38px;
          height: 38px;
          border: none;
          background: transparent;
          border-radius: 8px;
          cursor: pointer;
          padding: 0;
          transition: background 0.2s;
        }
        @media (min-width: 768px) {
          .hamburger-btn { display: none; }
        }
        .hamburger-btn:hover {
          background: rgba(0,0,0,0.05);
        }
        .hamburger-icon {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .hamburger-icon span {
          display: block;
          width: 20px;
          height: 1.5px;
          background: #1a1a1a;
          border-radius: 2px;
          transition: transform 0.3s ease, opacity 0.3s ease, width 0.3s ease;
          transform-origin: center;
        }
        .hamburger-icon.open span:nth-child(1) {
          transform: translateY(6.5px) rotate(45deg);
        }
        .hamburger-icon.open span:nth-child(2) {
          opacity: 0;
          transform: scaleX(0);
        }
        .hamburger-icon.open span:nth-child(3) {
          transform: translateY(-6.5px) rotate(-45deg);
        }

        /* MOBILE OVERLAY */
        .mobile-overlay {
          position: fixed;
          inset: 0;
          z-index: 60;
          background: rgba(0,0,0,0.25);
          backdrop-filter: blur(4px);
          -webkit-backdrop-filter: blur(4px);
          transition: opacity 0.3s ease;
        }
        .mobile-overlay.visible { opacity: 1; }
        .mobile-overlay.hidden {
          opacity: 0;
          pointer-events: none;
        }

        /* MOBILE DRAWER */
        .mobile-drawer {
          position: fixed;
          top: 0; right: 0;
          z-index: 70;
          height: 100%;
          width: 280px;
          background: #fff;
          padding: 24px;
          transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1);
          display: flex;
          flex-direction: column;
        }
        .mobile-drawer.open { transform: translateX(0); }
        .mobile-drawer.closed { transform: translateX(100%); }

        .drawer-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 36px;
        }

        .drawer-logo {
          font-family: 'DM Mono', monospace;
          font-size: 14px;
          font-weight: 500;
          color: #1a1a1a;
          text-decoration: none;
        }
        .drawer-logo span { color: #2563eb; }

        .close-btn {
          width: 32px;
          height: 32px;
          border: none;
          background: #f4f4f5;
          border-radius: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.2s;
        }
        .close-btn:hover { background: #e4e4e7; }
        .close-btn svg {
          width: 14px;
          height: 14px;
          stroke: #52525b;
        }

        .drawer-links {
          display: flex;
          flex-direction: column;
          gap: 2px;
          flex: 1;
        }
        .drawer-link {
          padding: 12px 14px;
          font-size: 15px;
          font-weight: 400;
          color: #3f3f46;
          text-decoration: none;
          border-radius: 10px;
          transition: background 0.15s, color 0.15s;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .drawer-link:hover {
          background: #f4f4f5;
          color: #1a1a1a;
        }
        .drawer-link.active {
          background: #eff6ff;
          color: #2563eb;
          font-weight: 500;
        }
        .drawer-link svg {
          width: 14px;
          height: 14px;
          opacity: 0.3;
        }
        .drawer-link.active svg { opacity: 0.7; }

        .drawer-divider {
          height: 1px;
          background: #f4f4f5;
          margin: 16px 0;
        }

        .drawer-cta {
          display: block;
          padding: 13px;
          text-align: center;
          font-size: 14px;
          font-weight: 500;
          color: #fff;
          background: #1a1a1a;
          border-radius: 10px;
          text-decoration: none;
          transition: background 0.2s;
        }
        .drawer-cta:hover { background: #2563eb; }

        .drawer-footer {
          margin-top: 24px;
          font-size: 11px;
          color: #a1a1aa;
          font-family: 'DM Mono', monospace;
          text-align: center;
        }
      `}</style>

      <div className="header-root">
        {/* NAVBAR */}
        <nav className={`nav-bar ${scrolled ? "scrolled" : ""}`}>
          <div className="nav-inner">

            {/* LOGO */}
            <Link to="/" className="logo-link">
              <div className="logo-mark">
                <svg viewBox="0 0 14 14" fill="none">
                  <rect x="1" y="1" width="5" height="5" rx="1" fill="white" opacity="0.9"/>
                  <rect x="8" y="1" width="5" height="5" rx="1" fill="white" opacity="0.5"/>
                  <rect x="1" y="8" width="5" height="5" rx="1" fill="white" opacity="0.5"/>
                  <rect x="8" y="8" width="5" height="5" rx="1" fill="#60a5fa" opacity="0.9"/>
                </svg>
              </div>
              <span className="logo-text">quem<span>vota</span></span>
            </Link>

            {/* DESKTOP LINKS */}
            <div className="desktop-links">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  to={link.href}
                  className={`nav-link ${pathname === link.href ? "active" : ""}`}
                >
                  {link.name}
                </Link>
              ))}
              <Link to="/politicos" className="cta-btn">
                Explorar dados
                <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M2 6h8M6 2l4 4-4 4"/>
                </svg>
              </Link>
            </div>

            {/* HAMBURGER */}
            <button
              className="hamburger-btn"
              onClick={() => setOpen((v) => !v)}
              aria-label="Menu"
            >
              <div className={`hamburger-icon ${open ? "open" : ""}`}>
                <span /><span /><span />
              </div>
            </button>

          </div>
        </nav>

        {/* OVERLAY */}
        <div
          className={`mobile-overlay ${open ? "visible" : "hidden"}`}
          onClick={() => setOpen(false)}
        />

        {/* DRAWER */}
        <div className={`mobile-drawer ${open ? "open" : "closed"}`}>
          <div className="drawer-header">
            <Link to="/" className="drawer-logo">quem<span>vota</span></Link>
            <button className="close-btn" onClick={() => setOpen(false)}>
              <svg viewBox="0 0 14 14" fill="none" strokeWidth="1.8" strokeLinecap="round">
                <path d="M2 2l10 10M12 2L2 12"/>
              </svg>
            </button>
          </div>

          <div className="drawer-links">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.href}
                className={`drawer-link ${pathname === link.href ? "active" : ""}`}
              >
                {link.name}
                <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M2 6h8M6 2l4 4-4 4"/>
                </svg>
              </Link>
            ))}

            <div className="drawer-divider" />

            <Link to="/politicos" className="drawer-cta">
              Explorar dados →
            </Link>
          </div>

          <div className="drawer-footer">quemvota.com.br</div>
        </div>
      </div>
    </>
  );
}