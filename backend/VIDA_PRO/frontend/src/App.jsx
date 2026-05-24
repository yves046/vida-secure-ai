import { useEffect, useState } from "react";
import API from "./api";

function Dashboard() {
  const [email, setEmail] = useState("Chargement...");
  const [stats, setStats] = useState({ cameras: 0, alerts: 0 });
  const [alerts, setAlerts] = useState([]);

  // 🔹 FETCH USER
  const fetchUser = async () => {
    try {
      const token = localStorage.getItem("token");

      if (!token) {
        setEmail("Non connecté");
        return;
      }

      const res = await API.get("/dashboard", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setEmail(res.data.email);

    } catch (err) {
      console.log(err);
      setEmail("Erreur serveur");
    }
  };

  // 🔹 FETCH STATS
  const fetchStats = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await API.get("/stats", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setStats(res.data);

    } catch (err) {
      console.log(err);
    }
  };

  // 🔹 FETCH ALERTS
  const fetchAlerts = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await API.get("/alerts", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setAlerts(res.data);

    } catch (err) {
      console.log(err);
    }
  };

  // 🔹 LOAD ALL DATA
  useEffect(() => {
    fetchUser();
    fetchStats();
    fetchAlerts();
  }, []);

  // 🔹 LOGOUT
  const logout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  // 🔹 TEST ALERT
  const triggerAlert = async () => {
    try {
      const token = localStorage.getItem("token");

      await API.post("/test-alert", {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      alert("Alerte envoyée");

      // 🔥 recharge les alertes après clic
      fetchAlerts();
      fetchStats();

    } catch (err) {
      console.log(err);
      alert("Erreur alerte");
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex">
      <aside className="w-64 bg-gray-900 p-6">
        <h2 className="text-2xl font-bold mb-8">VIDA</h2>

        <ul className="space-y-4 text-gray-300">
          <li>Dashboard</li>
          <li>Caméras</li>
          <li>Alertes</li>
          <li>Rapports</li>
          <li>Facturation</li>
        </ul>

        <button
          onClick={logout}
          className="mt-10 w-full bg-red-600 p-2 rounded"
        >
          Déconnexion
        </button>
      </aside>

      <main className="flex-1 p-10">
        <h1 className="text-4xl font-bold">Dashboard Client</h1>

        <p className="text-green-400 mt-4">
          Connecté : {email}
        </p>

        <div className="mt-8 grid grid-cols-3 gap-6">
          <div className="bg-gray-800 p-6 rounded-xl">
            <p className="text-gray-400">Caméras</p>
            <h2 className="text-3xl font-bold mt-2">{stats.cameras}</h2>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl">
            <p className="text-gray-400">Alertes</p>
            <h2 className="text-3xl font-bold mt-2">{stats.alerts}</h2>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl">
            <p className="text-gray-400">Abonnement</p>
            <h2 className="text-2xl font-bold mt-2">Actif</h2>
          </div>
        </div>

        <button
          onClick={triggerAlert}
          className="bg-yellow-500 text-black p-3 rounded mt-6"
        >
          Tester alerte
        </button>

        <div className="mt-10">
          <h2 className="text-2xl font-bold mb-4">Alertes récentes</h2>

          {alerts.length === 0 ? (
            <p className="text-gray-400">Aucune alerte</p>
          ) : (
            <div className="space-y-3">
              {alerts.map((a) => (
                <div key={a.id} className="bg-gray-800 p-4 rounded">
                  <p className="text-red-400 font-bold">{a.type}</p>
                  <p className="text-gray-400 text-sm">{a.timestamp}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;