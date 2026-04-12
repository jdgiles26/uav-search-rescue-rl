import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import * as api from "../api/client";
import { useMissionStore } from "../store/missionStore";

export default function DocumentIngest() {
  const navigate = useNavigate();
  const { fetchMissions, fetchAlerts } = useMissionStore();

  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{
    alert_id: number;
    document_name: string;
    extracted: Record<string, unknown>;
    confidence: number;
    mission_id?: number;
    message: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoSolve, setAutoSolve] = useState(true);

  const onDrop = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;
      setUploading(true);
      setError(null);
      setResult(null);

      try {
        const res = await api.ingestDocument(files[0], autoSolve);
        setResult(res);
        fetchMissions();
        fetchAlerts();
      } catch (e: any) {
        setError(e.message);
      } finally {
        setUploading(false);
      }
    },
    [autoSolve]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
    },
    maxFiles: 1,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-cyan-400">
        Document Intake
      </h1>
      <p className="text-sm text-gray-400">
        Upload a SAR alert document (PDF or text). The system will
        automatically extract mission parameters, create an alert, and
        generate a mission for analyst review.
      </p>

      {/* Options */}
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={autoSolve}
            onChange={(e) => setAutoSolve(e.target.checked)}
            className="rounded border-gray-600 bg-white/5"
          />
          Auto-solve after ingestion
        </label>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`glass-card-hover flex h-52 cursor-pointer flex-col items-center justify-center gap-3 border-dashed ${
          isDragActive ? "border-cyan-400 bg-cyan-500/5" : ""
        }`}
      >
        <input {...getInputProps()} />
        <svg
          className="h-10 w-10 text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        {uploading ? (
          <p className="text-cyan-400">Processing document...</p>
        ) : isDragActive ? (
          <p className="text-cyan-400">Drop the file here</p>
        ) : (
          <>
            <p className="text-gray-400">
              Drag & drop a SAR document, or click to browse
            </p>
            <p className="text-xs text-gray-500">PDF, TXT, MD</p>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="glass-card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-green-400">
              Document Processed Successfully
            </h3>
            <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs text-cyan-400">
              Confidence: {(result.confidence * 100).toFixed(0)}%
            </span>
          </div>

          <p className="text-sm text-gray-300">{result.message}</p>

          {/* Extracted data */}
          <div>
            <h4 className="mb-2 text-sm font-medium text-gray-400">
              Extracted Parameters
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(result.extracted)
                .filter(([, v]) => v != null)
                .map(([key, val]) => (
                  <div
                    key={key}
                    className="flex justify-between rounded-lg border border-white/5 bg-white/[0.02] px-3 py-1.5"
                  >
                    <span className="text-xs text-gray-500">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span className="text-sm font-mono text-gray-200">
                      {String(val)}
                    </span>
                  </div>
                ))}
            </div>
          </div>

          <div className="flex gap-3">
            {result.mission_id && (
              <button
                className="btn-primary"
                onClick={() => navigate("/review")}
              >
                Review Mission #{result.mission_id}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Pipeline diagram */}
      <div className="glass-card">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
          Ingestion Pipeline
        </h3>
        <div className="flex items-center gap-3 text-sm">
          {[
            "Upload Document",
            "Extract Text",
            "AI Parameter Extraction",
            "Create Alert",
            "Generate Mission",
            "Auto-Solve (optional)",
            "Analyst Review",
          ].map((step, i, arr) => (
            <div key={step} className="flex items-center gap-3">
              <div className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-gray-300">
                {step}
              </div>
              {i < arr.length - 1 && (
                <span className="text-gray-600">&#8594;</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
