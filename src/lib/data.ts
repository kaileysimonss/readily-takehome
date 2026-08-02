import fs from "fs";
import path from "path";

export interface PpChunk {
  chunkId: string;
  doc: string;
  docTitle: string;
  section: string;
  page: number;
  text: string;
}

export interface MatchCandidate {
  chunkId: string;
  doc: string;
  section: string;
  score: number;
}

export type Verdict = "supports" | "partial" | "contradicts" | "gap" | "error";

// Normalized shape shared by both the ECM-obligation matches and the
// questionnaire matches - they're structurally identical (a statement
// checked against P&P coverage) once the source-specific id/text field
// names are mapped onto a common "id"/"statement".
export interface MatchItem {
  id: string;
  doc: string;
  docTitle: string;
  page: number;
  statement: string;
  number?: number; // questionnaire only: its position in the Submission Review Form
  reference?: string; // questionnaire only: the APL citation, e.g. "APL 25-008, page 1"
  verdict: Verdict;
  matchedChunkId: string | null;
  matchedDoc: string | null;
  matchedSection: string | null;
  explanation: string;
  citationVerified: boolean | null;
  candidates: MatchCandidate[];
}

interface RawEcmMatch {
  obligationId: string;
  doc: string;
  docTitle: string;
  page: number;
  obligation: string;
  verdict: Verdict;
  matchedChunkId: string | null;
  matchedDoc: string | null;
  matchedSection: string | null;
  explanation: string;
  citationVerified: boolean | null;
  candidates: MatchCandidate[];
}

interface RawQuestionMatch {
  questionId: string;
  doc: string;
  docTitle: string;
  page: number;
  number: number;
  question: string;
  reference: string | null;
  verdict: Verdict;
  matchedChunkId: string | null;
  matchedDoc: string | null;
  matchedSection: string | null;
  explanation: string;
  citationVerified: boolean | null;
  candidates: MatchCandidate[];
}

const DATA_DIR = path.join(process.cwd(), "data");

let ppChunkIndex: Map<string, PpChunk> | null = null;
function getPpChunkIndex(): Map<string, PpChunk> {
  if (!ppChunkIndex) {
    const raw = fs.readFileSync(
      path.join(DATA_DIR, "plan_policies", "chunks-meta.json"),
      "utf-8"
    );
    const chunks: PpChunk[] = JSON.parse(raw);
    ppChunkIndex = new Map(chunks.map((c) => [c.chunkId, c]));
  }
  return ppChunkIndex;
}

export function getPpChunk(chunkId: string): PpChunk | undefined {
  return getPpChunkIndex().get(chunkId);
}

let ecmMatches: MatchItem[] | null = null;
export function getEcmMatches(): MatchItem[] {
  if (!ecmMatches) {
    const raw = fs.readFileSync(path.join(DATA_DIR, "ecm_guide", "matches.json"), "utf-8");
    const parsed: RawEcmMatch[] = JSON.parse(raw);
    ecmMatches = parsed.map((m) => ({
      id: m.obligationId,
      doc: m.doc,
      docTitle: m.docTitle,
      page: m.page,
      statement: m.obligation,
      verdict: m.verdict,
      matchedChunkId: m.matchedChunkId,
      matchedDoc: m.matchedDoc,
      matchedSection: m.matchedSection,
      explanation: m.explanation,
      citationVerified: m.citationVerified ?? null,
      candidates: m.candidates,
    }));
  }
  return ecmMatches;
}

let questionnaireMatches: MatchItem[] | null = null;
export function getQuestionnaireMatches(): MatchItem[] {
  if (!questionnaireMatches) {
    const raw = fs.readFileSync(path.join(DATA_DIR, "questionnaire", "matches.json"), "utf-8");
    const parsed: RawQuestionMatch[] = JSON.parse(raw);
    questionnaireMatches = parsed.map((m) => ({
      id: m.questionId,
      doc: m.doc,
      docTitle: m.docTitle,
      page: m.page,
      statement: m.question,
      number: m.number,
      reference: m.reference ?? undefined,
      verdict: m.verdict,
      matchedChunkId: m.matchedChunkId,
      matchedDoc: m.matchedDoc,
      matchedSection: m.matchedSection,
      explanation: m.explanation,
      citationVerified: m.citationVerified ?? null,
      candidates: m.candidates,
    }));
    questionnaireMatches.sort((a, b) => (a.number ?? 0) - (b.number ?? 0));
  }
  return questionnaireMatches;
}
