"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface FileUploadProps {
  accept: Record<string, string[]>;
  label: string;
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function FileUpload({ accept, label, onFile, disabled }: FileUploadProps) {
  const [fileName, setFileName] = useState<string | null>(null);

  const onDrop = useCallback(
    (files: File[]) => {
      if (files[0]) {
        setFileName(files[0].name);
        onFile(files[0]);
      }
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxFiles: 1,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <input {...getInputProps()} />
      {fileName ? (
        <p className="text-sm text-gray-700">
          <span className="font-medium">Selected:</span> {fileName}
        </p>
      ) : (
        <p className="text-sm text-gray-500">
          {isDragActive ? "Drop here..." : label}
        </p>
      )}
    </div>
  );
}
