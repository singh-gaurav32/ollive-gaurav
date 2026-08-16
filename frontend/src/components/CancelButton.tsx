export function CancelButton({ onCancel }: { onCancel: () => void }) {
  return (
    <button
      onClick={onCancel}
      data-testid="cancel-button"
      className="rounded bg-red-100 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-200"
    >
      Cancel
    </button>
  );
}
