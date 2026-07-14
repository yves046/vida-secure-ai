import { useEffect, useState } from "react";
import API from "../api";

function CameraManager() {
  const [cameras, setCameras] = useState([]);

  const [cameraName, setCameraName] = useState("");
  const [siteName, setSiteName] = useState("");
  const [location, setLocation] = useState("");
  const [rtspUrl, setRtspUrl] = useState("");

  const loadCameras = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await API.get("/cameras", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setCameras(res.data);

    } catch (err) {

        if (err.response?.status === 400) {
          alert(err.response.data.detail);
          return;
        }

      console.log(err);
    }
  };

  const addCamera = async () => {
    try {
      const token = localStorage.getItem("token");

      await API.post(
        "/cameras",
        {
          camera_name: cameraName,
          site_name: siteName,
          location: location,
          rtsp_url: rtspUrl,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setCameraName("");
      setSiteName("");
      setLocation("");
      setRtspUrl("");

      loadCameras();

    } catch (err) {

      if (err.response?.status === 400) {
        alert(err.response.data.detail);
        return;
      }

      console.log(err);
      alert("Impossible d'ajouter la caméra.");
    }
  };

  useEffect(() => {
    loadCameras();
  }, []);

  return (
    <div className="mt-10">

      <h2 className="text-2xl font-bold mb-5">
        Caméras
      </h2>      

      <div className="bg-gray-900 p-6 rounded-xl mb-8 border border-gray-700">

        <h3 className="text-xl font-bold mb-4">
          Ajouter une caméra
        </h3>

        <input
          type="text"
          placeholder="Nom de la caméra"
          value={cameraName}
          onChange={(e) => setCameraName(e.target.value)}
          className="w-full p-3 rounded bg-gray-800 mb-3"
        />

        <input
          type="text"
          placeholder="Site (ex. Entrepôt principal)"
          value={siteName}
          onChange={(e) => setSiteName(e.target.value)}
          className="w-full p-3 rounded bg-gray-800 mb-3"
        />

        <input
          type="text"
          placeholder="Emplacement (ex. Entrée nord)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="w-full p-3 rounded bg-gray-800 mb-3"
        />

        <input
          type="text"
          placeholder="URL RTSP"
          value={rtspUrl}
          onChange={(e) => setRtspUrl(e.target.value)}
          className="w-full p-3 rounded bg-gray-800 mb-4"
        />

        <button
          onClick={addCamera}
          className="bg-blue-600 hover:bg-blue-700 px-5 py-3 rounded-lg font-semibold"
        >
          Ajouter la caméra
        </button>

      </div>

      {cameras.length === 0 ? (
        <p className="text-gray-400">
          Aucune caméra enregistrée.
        </p>
      ) : (
        <div className="space-y-4">
          {cameras.map((cam) => (
            <div
              key={cam.id}
              className="bg-gray-800 rounded-xl p-5 border border-gray-700"
            >
              <h3 className="text-xl font-bold">
                {cam.camera_name}
              </h3>

              <p className="text-gray-300 mt-2">
                Site : {cam.site_name || "Non renseigné"}
              </p>

              <p className="text-gray-300">
                Emplacement : {cam.location || "Non renseigné"}
              </p>

              <p className="text-green-400 mt-2">
                {cam.status}
              </p>

            </div>
          ))}
        </div>
      )}

    </div>
  );
}

export default CameraManager;
