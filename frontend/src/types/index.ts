// TypeScript interfaces for DeceptiScan frontend application
// Based on design specifications from design.md

export interface ArticleInput {
  // Primary input
  content: string;           // Required: Article text (max 50,000 chars)
  sourceUrl?: string;        // Optional: Source URL if available
  title?: string;           // Optional: Article title
  
  // Metadata
  language: string;         // Default: "en"
  contentType: 'text' | 'url';  // Input type
}

export type Classification = 'reliable' | 'mixed' | 'unreliable' | 'unknown' | 'unverified_style_estimate';

export interface SentenceAnalysis {
  index: number;           // Position in original text
  text: string;           // The sentence
  isSuspicious: boolean;  // Flagged as potentially misleading
  score: number;          // Individual sentence score (0-100)
  confidence: number;     // 0-1
  category: string;       // "factual" | "opinion" | "claim" | "context"
  flags: string[];        // Specific flags raised
  explanation: string;    // Human-readable explanation
}

export interface SimilarClaim {
  text: string;
  score: number;
  sourceUrl?: string;
}

export interface AnalysisResult {
  // Identifiers
  id: string;               // UUID
  analysisVersion?: string;  // e.g., "1.0.0"
  
  // Scores
  authenticityScore: number;       // 0-100 (higher = more reliable)
  confidence?: number;             // 0-1 (model confidence)
  confidenceScore?: number;        // 0-1 (alias for confidence)
  classification: Classification;  // Primary classification
  warning?: string;                // Warning for low confidence or special estimates
  
  // Detailed analysis
  sentenceAnalysis: SentenceAnalysis[];
  overallSummary?: string;         // Brief explanation
  
  // Metadata
  processingTime: number;          // milliseconds
  analyzedAt: string;              // ISO 8601 timestamp
  modelVersion: string;            // ML model version
  is_cached?: boolean;
  similar_claims?: SimilarClaim[] | null;
  retrieval_status?: string;
}

export interface UserFeedback {
  id: string;
  analysisId: string;     // Reference to analysis result
  userId: string | null;  // Anonymous if null
  
  feedback: {
    type: 'helpful' | 'incorrect' | 'disputed';
    correctedClassification?: Classification;
    comment?: string;
  };
  
  createdAt: string;
}

export interface ScoreMeter {
  value: number;           // 0-100
  label: string;           // "Highly Reliable" | "Mostly Reliable" | "Mixed" | "Suspicious" | "Unreliable"
  color: string;           // Hex color code
  interpretation: string;  // User-friendly explanation
  
  // Thresholds
  thresholds: {
    reliable: number;      // >= 75
    mixed: number;         // 40-74
    unreliable: number;    // < 40
  };
}

export interface HighlightedSegment {
  text: string;
  startIndex: number;
  endIndex: number;
  classification: 'reliable' | 'suspicious' | 'neutral';
  confidence: number;
  explanation: string;
}

export interface User {
  id: string;
  email: string;
  createdAt: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirmPassword: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}

// Analysis History types
export interface AnalysisHistoryItem {
  id: string;
  authenticityScore: number;
  classification: Classification;
  createdAt: string;
  title?: string;
  sourceUrl?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Component Props interfaces
export interface ArticleInputProps {
  onSubmit: (text: string) => Promise<void>;
  isLoading: boolean;
}

export interface AnalysisResultProps {
  result: AnalysisResult;
  highlightedText: HighlightedSegment[];
}

export interface ScoreMeterProps {
  score: number;  // 0-100
  label: string;  // "Reliable", "Suspicious", etc.
  confidence?: number;  // 0-1 (model confidence)
}