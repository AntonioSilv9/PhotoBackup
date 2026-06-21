"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [photos, setPhotos] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const API =
    process.env.NEXT_PUBLIC_API_URL ||
    "http://192.168.1.42:8081";

  useEffect(() => {
    load();
  }, []);

  async function load() {
    const res = await fetch(`${API}/photos`);
    setPhotos(await res.json());
  }

  async function upload() {
    if (!files.length) return;

    const form = new FormData();
    files.forEach(f => form.append("files", f));

    await fetch(`${API}/upload`, {
      method: "POST",
      body: form,
    });

    setFiles([]);
    load();
  }

  function next() {
    if (selectedId === null) return;

    const index = photos.findIndex(p => p.id === selectedId);
    if (index < photos.length - 1) {
      setSelectedId(photos[index + 1].id);
    }
  }

  function prev() {
    if (selectedId === null) return;

    const index = photos.findIndex(p => p.id === selectedId);
    if (index > 0) {
      setSelectedId(photos[index - 1].id);
    }
  }

  let startX = 0;

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#0a0a0a",
        color: "white",
        fontFamily: "system-ui",
        padding: 20,
      }}
    >
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22 }}>📷 Photo Backup</h1>
      </div>

      <div
        style={{
          display: "flex",
          gap: 10,
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={(e) =>
            setFiles(Array.from(e.target.files || []))
          }
          style={{ color: "white" }}
        />

        <button
          onClick={upload}
          style={{
            padding: "8px 14px",
            borderRadius: 10,
            border: "none",
            background: "#2563eb",
            color: "white",
            fontWeight: 600,
          }}
        >
          Upload
        </button>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
          gap: 10,
        }}
      >
        {photos.map((p) => (
          <img
            key={p.id}
            src={`${API}/photo/${p.id}/thumb`}
            onClick={() => setSelectedId(p.id)}
            style={{
              width: "100%",
              aspectRatio: "1/1",
              objectFit: "cover",
              borderRadius: 12,
              cursor: "pointer",
            }}
          />
        ))}
      </div>

      {selectedId !== null && (
        <div
          onClick={() => setSelectedId(null)}
          onTouchStart={(e) => (startX = e.touches[0].clientX)}
          onTouchEnd={(e) => {
            const diff = startX - e.changedTouches[0].clientX;

            if (diff > 50) next();
            if (diff < -50) prev();
          }}
          style={{
            position: "fixed",
            inset: 0,
            background: "black",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <img
            src={`${API}/photo/${selectedId}`}
            style={{
              maxWidth: "95%",
              maxHeight: "95%",
              objectFit: "contain",
            }}
          />
        </div>
      )}
    </main>
  );
}