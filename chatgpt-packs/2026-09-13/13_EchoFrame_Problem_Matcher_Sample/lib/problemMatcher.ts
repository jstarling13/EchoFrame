export type MatcherDocument = {
  id: string;
  source: "industry-selector" | "services";
  path: string;
  text: string;
};

export type MatcherResult = MatcherDocument & {
  score: number;
  matchedTerms: string[];
};

const STOP_WORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "been",
  "but",
  "by",
  "can",
  "do",
  "for",
  "from",
  "had",
  "has",
  "have",
  "help",
  "how",
  "i",
  "in",
  "is",
  "it",
  "me",
  "my",
  "of",
  "on",
  "or",
  "our",
  "so",
  "that",
  "the",
  "their",
  "this",
  "to",
  "we",
  "what",
  "when",
  "where",
  "with",
  "would",
  "you",
  "your",
]);

function tokens(value: string): string[] {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/[\s-]+/)
    .filter((word) => word.length > 1 && !STOP_WORDS.has(word));
}

function stableId(source: MatcherDocument["source"], path: string): string {
  let hash = 2166136261;
  for (const character of `${source}:${path}`) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return `${source}-${(hash >>> 0).toString(36)}`;
}

/** Extracts only existing strings. Object keys are paths, never visitor-facing copy. */
export function documentsFromExport(
  value: unknown,
  source: MatcherDocument["source"],
  path = source,
): MatcherDocument[] {
  if (typeof value === "string") {
    const text = value.trim();
    if (text.length < 18) return [];
    return [{ id: stableId(source, path), source, path, text }];
  }

  if (Array.isArray(value)) {
    return value.flatMap((item, index) =>
      documentsFromExport(item, source, `${path}[${index}]`),
    );
  }

  if (value && typeof value === "object") {
    return Object.entries(value).flatMap(([key, item]) =>
      documentsFromExport(item, source, `${path}.${key}`),
    );
  }

  return [];
}

function scoreDocument(
  query: string,
  document: MatcherDocument,
): MatcherResult {
  const queryTokens = [...new Set(tokens(query))];
  const documentTokens = [...new Set(tokens(document.text))];
  const documentSet = new Set(documentTokens);
  const normalizedQuery = queryTokens.join(" ");
  const normalizedDocument = documentTokens.join(" ");

  const exact = queryTokens.filter((term) => documentSet.has(term));
  const prefix = queryTokens.filter(
    (term) =>
      term.length >= 5 &&
      !documentSet.has(term) &&
      documentTokens.some(
        (candidate) =>
          candidate.length >= 5 &&
          (candidate.startsWith(term) || term.startsWith(candidate)),
      ),
  );

  const exactPoints = exact.reduce(
    (sum, term) => sum + Math.min(4, term.length / 2),
    0,
  );
  const prefixPoints = prefix.length * 1.25;
  const coverage = queryTokens.length ? exact.length / queryTokens.length : 0;
  const phraseBonus =
    normalizedQuery.length >= 8 && normalizedDocument.includes(normalizedQuery)
      ? 5
      : 0;

  return {
    ...document,
    score: exactPoints + prefixPoints + coverage * 3 + phraseBonus,
    matchedTerms: [...exact, ...prefix],
  };
}

export function matchProblem(
  query: string,
  documents: MatcherDocument[],
  options: { limit?: number; minimumScore?: number } = {},
): MatcherResult[] {
  const { limit = 3, minimumScore = 3.25 } = options;
  if (tokens(query).length < 2) return [];

  return documents
    .map((document) => scoreDocument(query, document))
    .filter((result) => result.score >= minimumScore)
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
    .filter(
      (result, index, all) =>
        all.findIndex((candidate) => candidate.text === result.text) === index,
    )
    .slice(0, limit);
}
