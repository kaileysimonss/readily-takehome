import { getMatches } from "@/lib/data";
import EcmWorkspace from "./EcmWorkspace";

export default function EcmPage() {
  const matches = getMatches();
  return <EcmWorkspace matches={matches} />;
}
