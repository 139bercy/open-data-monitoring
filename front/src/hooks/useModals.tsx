// hooks/useModals.ts
import { useCallback, useState } from "react";

export type CompareSnapshotsState = {
  isOpen: boolean;
  snapshotA?: any;
  snapshotB?: any;
};

export function useCompareSnapshotsModal() {
  const [state, setState] = useState<CompareSnapshotsState>({ isOpen: false });

  const open = useCallback((snapshotA: any, snapshotB: any) => {
    setState({ isOpen: true, snapshotA, snapshotB });
  }, []);

  const close = useCallback(() => {
    setState({ isOpen: false });
  }, []);

  return { ...state, open, close };
}
