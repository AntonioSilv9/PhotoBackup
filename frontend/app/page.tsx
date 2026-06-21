"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState("");
  const [photos, setPhotos] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);

  const API = process.env.NEXT_PUBLIC_API_URL || "http://192.168.1.42:8081";

  useEffect(() => {
    loadPhotos();
  }, []);

  async function loadPhotos() {
    const response = await fetch(`${API}/photos`);
    const data = await response.json();
    setPhotos(data);
  }

  async function upload() {
    if (files.length === 0) return;

    const formData = new FormData();

    files.forEach((file) => {
      formData.append("files", file);
    });

    const response = await fetch(`${API}/upload`, {
      method: "POST",
      body: formData,
    });

    setFiles([]);

    const data = await response.json();

    setResult(JSON.stringify(data, null, 2));
    loadPhotos();
  }

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Photo Backup</h1>

      <input
        type="file"
        accept="image/*"
        multiple
        onChange={(e) =>
          setFiles(Array.from(e.target.files || []))
        }
      />

      <br />
      <br />

      <button onClick={upload}>
        Upload
      </button>

      <pre>{result}</pre>

      <h2>Galeria</h2>

      {/* 🔥 GRID DA GALERIA */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, 200px)",
          gap: "10px",
          marginTop: "20px",
        }}
      >
        {photos.map((photo) => (
          <img
            key={photo.id}
            src={`${API}/photo/${photo.id}/thumb`}
            onClick={() => setSelected(photo)}
            style={{
              width: "200px",
              height: "200px",
              objectFit: "cover",
              cursor: "pointer",
            }}
          />
        ))}
      </div>

      {selected && (
        <div
          onClick={() => setSelected(null)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background: "black",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 9999,
          }}
        >
          <img
            src={`${API}/photo/${selected.id}`}
            style={{
              maxWidth: "95%",
              maxHeight: "95%",
            }}
          />
        </div>
      )}
    </main>
  );
}