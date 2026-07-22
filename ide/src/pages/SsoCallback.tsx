import { HandleSSOCallback } from "@clerk/react";
import { useNavigate } from "react-router";
import "./AuthPage.css";

export default function SsoCallback() {
  const navigate = useNavigate();

  return (
    <main className="auth-page">
      <section className="auth-card" aria-live="polite">
        <div className="auth-card__brand">
          <span>L00m AI</span>
          <h1>Finishing sign-in</h1>
          <p>Securely connecting your session.</p>
        </div>
        <HandleSSOCallback
          navigateToApp={({ decorateUrl }) => navigate(decorateUrl("/"))}
          navigateToSignIn={() => navigate("/sign-in")}
          navigateToSignUp={() => navigate("/sign-up")}
        />
      </section>
    </main>
  );
}
