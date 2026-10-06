import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { uploadDocument } from "../utils/api";

export default function FileUpload({ onUploadSuccess }) {
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [message, setMessage] = useState("");

  const onDrop = useCallback(async (acceptedFiles) => {
    if (!acceptedFiles.length) return;
    const file = acceptedFiles[0];

    setStatus("uploading");
    setMessage(`Uploading "${file.name}"...`);

    try {
      const result = await uploadDocument(file);
      setStatus("success");
      setMessage(`✓ "${result.filename}" indexed into ${result.num_chunks} chunks`);
      onUploadSuccess(result);
    } catch (err) {
      setStatus("error");
      const serverMessage = err.response?.data?.detail;
      const networkMessage = err.message;
      setMessage(serverMessage || networkMessage || "Upload failed. Please try again.");
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
    },
    maxFiles: 1,
    disabled: status === "uploading",
  });

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200
          ${isDragActive ? "border-orange-400 bg-orange-50" : "border-stone-300 hover:border-orange-400 hover:bg-orange-50/50"}
          ${status === "uploading" ? "opacity-60 cursor-not-allowed" : ""}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2">
          {status === "uploading" ? (
            <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
          ) : (
            <Upload className="w-8 h-8 text-stone-400" />
          )}
          <p className="text-sm text-stone-600 font-medium">
            {isDragActive ? "Drop it here!" : "Drag & drop or click to upload"}
          </p>
          <p className="text-xs text-stone-400">PDF, DOCX, TXT, MD — max 20MB</p>
        </div>
      </div>

      {message && (
        <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg
          ${status === "success" ? "bg-green-50 text-green-700" : ""}
          ${status === "error" ? "bg-red-50 text-red-700" : ""}
          ${status === "uploading" ? "bg-orange-50 text-orange-700" : ""}
        `}>
          {status === "success" && <CheckCircle className="w-4 h-4 shrink-0" />}
          {status === "error" && <AlertCircle className="w-4 h-4 shrink-0" />}
          {status === "uploading" && <Loader2 className="w-4 h-4 shrink-0 animate-spin" />}
          <span>{message}</span>
        </div>
      )}
    </div>
  );
}
