import { getEcmMatches } from "@/lib/data";
import MatchWorkspace from "@/components/MatchWorkspace";

export default function EcmPage() {
  const matches = getEcmMatches();
  return (
    <MatchWorkspace
      items={matches}
      title="P&P vs. ECM Policy Guide"
      unitLabelSingular="obligation"
      unitLabelPlural="obligations"
      sourceLabel="the ECM Policy Guide"
    />
  );
}
