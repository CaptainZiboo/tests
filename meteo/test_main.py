# test_main.py
import requests
from unittest.mock import patch, mock_open
from main import (
    est_pair, convertir_minutes,
    analyser_donnees_meteo, appeler_api_meteo,
    sauvegarder_resultats, afficher_graphique_temperature
)


def test_est_pair():
    assert est_pair(10)
    assert est_pair(0)
    assert not est_pair(3)


def test_convertir_minutes():
    assert convertir_minutes(30) == "30 minutes"
    assert convertir_minutes(70) == "1 heure(s) 10 minutes"
    assert convertir_minutes(130) == "2 heure(s) 10 minutes"
    assert convertir_minutes(60) == "1 heure(s) 0 minutes"

def test_appeler_api_meteo_comportement():
    latitude = 48.8566
    longitude = 2.3522

    # --- Cas 1 : appel réussi ---
    reponse_mock = {
        "daily": {
            "time": ["2025-07-01", "2025-07-02"],
            "temperature_2m_max": [25.0, 26.0],
            "temperature_2m_min": [15.0, 16.0],
            "precipitation_sum": [0.0, 1.2]
        }
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = reponse_mock
        resultat = appeler_api_meteo(latitude, longitude)
        assert isinstance(resultat, dict)
        assert resultat["daily"]["temperature_2m_max"] == [25.0, 26.0]

    # --- Cas 2 : appel échoue (erreur réseau) ---
    with patch("requests.get", side_effect=requests.RequestException("Erreur réseau")):
        resultat = appeler_api_meteo(latitude, longitude)
        assert resultat is None