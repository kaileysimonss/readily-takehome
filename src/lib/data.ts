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

export interface Match {
  obligationId: string;
  doc: string;
  docTitle: string;
  page: number;
  obligation: string;
  verdict: "supports" | "partial" | "contradicts" | "gap" | "error";
  matchedChunkId: string | null;
  matchedDoc: string | null;
  matchedSection: string | null;
  explanation: string;
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

let matches: Match[] | null = null;
export function getMatches(): Match[] {
  if (!matches) {
    const raw = fs.readFileSync(path.join(DATA_DIR, "ecm_guide", "matches.json"), "utf-8");
    matches = JSON.parse(raw);
  }
  return matches!;
}
