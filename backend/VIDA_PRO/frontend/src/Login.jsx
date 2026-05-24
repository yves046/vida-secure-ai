import { useState } from "react";
import API from "./api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const login = async () => {
  try {
    const body = `email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;

    const res = await fetch("http://127.0.0.1:8000/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: body
    });

    const data = await res.json();

    console.log(data);

    if (res.ok) {
      localStorage.setItem("token", data.access_token);
      alert("Connexion réussie");
      window.location.href = "/dashboard";
    } else {
      alert("Erreur connexion");
    }

  } catch (err) {
    console.log(err);
    alert("Erreur réseau");
  }
};

  return (
    <div className="min-h-screen bg-black flex justify-center items-center">
      <div className="bg-zinc-900 p-8 rounded-xl w-96">
        <h1 className="text-white text-2xl mb-6">Connexion VIDA</h1>

        <input
          className="w-full p-3 mb-3 rounded"
          placeholder="Email"
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          className="w-full p-3 mb-4 rounded"
          placeholder="Mot de passe"
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          onClick={login}
          className="w-full bg-blue-600 text-white p-3 rounded"
        >
          Se connecter
        </button>
      </div>
    </div>
  );
}