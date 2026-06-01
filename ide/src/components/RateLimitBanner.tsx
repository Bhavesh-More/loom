import MaterialIcon from './MaterialIcon'

function RateLimitBanner() {
  return (
    <section className="rate-limit" aria-label="Message limit">
      <div className="rate-limit__icon">
        <MaterialIcon name="speed" />
      </div>
      <div className="rate-limit__copy">
        <p>You're out of Foxy messages</p>
        <span>
          Your rate limit resets on 1 Jul 2026, 16:29. To continue using Foxy,
          upgrade to Plus today.
        </span>
      </div>
    </section>
  )
}

export default RateLimitBanner
