export default function ThemeToggle({ onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="button-secondary h-10 min-w-[112px]"
      aria-label="Toggle theme"
    >
      Theme
      <span className="ml-2 h-2 w-2 rounded-full bg-[var(--accent-info)]" />
    </button>
  );
}
