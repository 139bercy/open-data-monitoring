import { SnapshotVersion } from "../types/datasets";

export function calculateDownloadsPerDay(
  snapshots: SnapshotVersion[] | null | undefined
): number | null {
  if (!snapshots || snapshots.length < 2) return null;
  const validSnapshots = snapshots.filter(
    (s) => s.downloadsCount !== null && s.downloadsCount !== undefined
  );

  if (validSnapshots.length < 2) return null;
  const sorted = [...validSnapshots].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const firstSnapshot = sorted[0];
  const lastSnapshot = sorted[sorted.length - 1];
  const startDate = new Date(firstSnapshot.timestamp);
  const endDate = new Date(lastSnapshot.timestamp);
  const daysDifference = Math.max(
    1,
    (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)
  );
  const downloadsDifference =
    (lastSnapshot.downloadsCount ?? 0) - (firstSnapshot.downloadsCount ?? 0);

  return Math.round((downloadsDifference / daysDifference) * 100) / 100;
}
