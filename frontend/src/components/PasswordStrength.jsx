/* Password strength meter: four colour bars plus the single most useful next
   improvement. Purely advisory feedback - the server independently enforces the
   8-character minimum, since client-side checks can be bypassed. */

const LEVELS = [
  { label: 'Too short', color: '#3F3F46', text: 'text-muted' },
  { label: 'Weak', color: '#E5484D', text: 'text-red-400' },
  { label: 'Fair', color: '#E8A33D', text: 'text-amber-400' },
  { label: 'Good', color: '#5BB98C', text: 'text-emerald-400' },
  { label: 'Strong', color: '#30A46C', text: 'text-emerald-400' },
]

export function scorePassword(password) {
  if (!password) return { score: 0, hint: null }
  if (password.length < 8) {
    return { score: 0, hint: `${8 - password.length} more character${8 - password.length === 1 ? '' : 's'} needed` }
  }

  const hasLower = /[a-z]/.test(password)
  const hasUpper = /[A-Z]/.test(password)
  const hasDigit = /\d/.test(password)
  const hasSymbol = /[^A-Za-z0-9]/.test(password)
  const variety = [hasLower, hasUpper, hasDigit, hasSymbol].filter(Boolean).length

  let score = 1
  if (password.length >= 10 && variety >= 2) score = 2
  if (password.length >= 12 && variety >= 3) score = 3
  if (password.length >= 14 && variety >= 3) score = 4
  if (/^(.)\1+$/.test(password)) score = 1 // all one repeated character

  let hint = null
  if (score < 4) {
    if (!hasUpper && !hasLower) hint = 'Add letters'
    else if (!hasDigit) hint = 'Add a number'
    else if (!hasSymbol) hint = 'Add a symbol like ! or ?'
    else if (password.length < 14) hint = 'Longer is stronger'
  }

  return { score, hint }
}

export default function PasswordStrength({ password }) {
  if (!password) return null

  const { score, hint } = scorePassword(password)
  const level = LEVELS[score]

  return (
    <div className="space-y-1.5 pt-0.5" aria-live="polite">
      <div className="flex gap-1.5">
        {[1, 2, 3, 4].map((bar) => (
          <span
            key={bar}
            className="h-1 flex-1 rounded-full transition-colors duration-300"
            style={{ backgroundColor: bar <= score ? level.color : '#26262A' }}
          />
        ))}
      </div>
      <div className="flex items-center justify-between gap-3">
        <span className={`text-[11px] font-medium ${level.text}`}>{level.label}</span>
        {hint && <span className="text-[11px] text-muted truncate">{hint}</span>}
      </div>
    </div>
  )
}
