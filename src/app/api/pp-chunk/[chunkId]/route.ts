import { NextRequest, NextResponse } from "next/server";
import { getPpChunk } from "@/lib/data";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ chunkId: string }> }
) {
  const { chunkId } = await params;
  const chunk = getPpChunk(decodeURIComponent(chunkId));
  if (!chunk) {
    return NextResponse.json({ error: "chunk not found" }, { status: 404 });
  }
  return NextResponse.json(chunk);
}
