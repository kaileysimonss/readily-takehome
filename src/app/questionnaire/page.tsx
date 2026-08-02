import { getQuestionnaireMatches } from "@/lib/data";
import MatchWorkspace from "@/components/MatchWorkspace";

export default function QuestionnairePage() {
  const matches = getQuestionnaireMatches();
  return (
    <MatchWorkspace
      items={matches}
      title="P&P vs. Submission Review Form"
      unitLabelSingular="question"
      unitLabelPlural="questions"
      sourceLabel="the DHCS Submission Review Form"
      storageKey="questionnaire"
    />
  );
}
