import CameraManager from "./components/CameraManager";
import { useEffect, useState } from "react";
import API from "./api";

function Dashboard() {
  const [email, setEmail] = useState("Chargement...");
  const [stats, setStats] = useState({ cameras: 0, alerts: 0 });
  const [alerts, setAlerts] = useState([]);
  const [evidenceUrls, setEvidenceUrls] = useState({});

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
      await fetchSecureEvidence(res.data);

    } catch (err) {
      console.log(err);
    }
  };

  // 🔹 FETCH SECURE EVIDENCE
  const fetchSecureEvidence = async (alertsData) => {
    const token = localStorage.getItem("token");

    if (!token) {
      return;
    }

    const urls = {};

    for (const alert of alertsData) {
      urls[alert.id] = {};

      for (const type of ["image", "video", "pdf"]) {
        const securePath = alert[type];

        if (!securePath) {
          continue;
        }

        try {
          const response = await API.get(securePath, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            responseType: "blob",
          });

          urls[alert.id][type] = URL.createObjectURL(
            response.data
          );

        } catch (err) {
          console.error(
            `Erreur chargement ${type} pour ${alert.id}`,
            err
          );
        }
      }
    }

    setEvidenceUrls((previousUrls) => {
      Object.values(previousUrls).forEach((evidence) => {
        Object.values(evidence).forEach((url) => {
          URL.revokeObjectURL(url);
        });
      });

      return urls;
    });
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
                <div
                  key={a.id}
                  className="bg-gray-800 p-5 rounded-xl border border-gray-700 shadow-lg"
                >
                  <div className="flex justify-between items-center">
                    <p 
                      className={`font-bold text-lg ${
                        a.type === "CRITIQUE"
                          ? "text-red-500"
                          : a.type === "ÉLEVÉ"
                          ? "text-orange-400"
                          : a.type === "MODÉRÉ"
                          ? "text-yellow-400"
                          : "text-green-400"
                      }`}
                    >
                      {a.type}
                    </p>

                    <span className="text-xs bg-red-500/20 text-red-300 px-2 py-1 rounded">
                      ALERTE
                    </span>
                  </div>

                  <p className="text-white mt-3">
                    📍 Zone : <span className="font-semibold">{a.zone}</span>
                  </p>

                  <p className="text-gray-300 mt-1">
                    👤 Personnes détectées : {a.persons}
                  </p>

                  <p className="text-gray-500 text-sm mt-3">
                    {a.timestamp}
                  </p>

                  {evidenceUrls[a.id]?.image && (
                    <img
                      src={evidenceUrls[a.id].image}
                      alt="Intrusion"
                      className="w-full rounded-lg mt-3"
                    />
                  )}
                  {evidenceUrls[a.id]?.video && (
                    <div className="mt-4">
                      <video
                        controls
                        src={evidenceUrls[a.id].video}
                        className="w-full rounded-lg border border-gray-700"
                      >
                        Votre navigateur ne supporte pas la vidéo.
                      </video>
                    </div>
                  )}
                  {evidenceUrls[a.id]?.pdf && (
                    <a
                      href={evidenceUrls[a.id].pdf}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-block mt-3 text-cyan-400"
                    >
                      Télécharger le rapport PDF
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        <CameraManager />
      </main>
    </div>
  );
}

export default Dashboard;
