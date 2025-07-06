# main.py
import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Optional


def est_pair(n: int) -> bool:
    return n % 2 == 0


def convertir_minutes(minutes: int) -> str:
    heures, minutes = divmod(minutes, 60)
    if heures == 0:
        return f"{minutes} minutes"
    return f"{heures} heure(s) {minutes} minutes"


def appeler_api_meteo(latitude: float, longitude: float, jours: int = 7) -> Optional[Dict]:
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "Europe/Paris",
            "forecast_days": jours
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erreur lors de l'appel API: {e}")
        return None


def analyser_donnees_meteo(donnees_meteo: Dict) -> Dict:
    if not donnees_meteo or 'daily' not in donnees_meteo:
        return {"erreur": "Données météo invalides"}

    daily = donnees_meteo['daily']
    temp_max = daily['temperature_2m_max']
    temp_min = daily['temperature_2m_min']
    precipitation = daily['precipitation_sum']

    temp_max_moy = sum(temp_max) / len(temp_max)
    temp_min_moy = sum(temp_min) / len(temp_min)

    return {
        "periode": {
            "debut": daily['time'][0],
            "fin": daily['time'][-1],
            "nb_jours": len(temp_max)
        },
        "temperatures": {
            "max_moyenne": round(temp_max_moy, 1),
            "min_moyenne": round(temp_min_moy, 1),
            "max_absolue": max(temp_max),
            "min_absolue": min(temp_min),
            "amplitude_moyenne": round(temp_max_moy - temp_min_moy, 1)
        },
        "precipitations": {
            "total_mm": sum(precipitation),
            "jours_avec_pluie": sum(p > 0 for p in precipitation),
            "pourcentage_jours_pluie": round(
                100 * sum(p > 0 for p in precipitation) / len(precipitation), 1)
        },
        "donnees_brutes": {
            "dates": daily['time'],
            "temp_max": temp_max,
            "temp_min": temp_min,
            "precipitation": precipitation
        }
    }


def sauvegarder_resultats(analyse: Dict, fichier: str = "meteo.json") -> bool:
    try:
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(analyse, f, indent=2, ensure_ascii=False)
        print(f"Résultats sauvegardés dans {fichier}")
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return False


def afficher_graphique_temperature(analyse: Dict):
    if "donnees_brutes" not in analyse:
        print("Erreur: données brutes manquantes pour le graphique")
        return

    donnees = analyse["donnees_brutes"]
    dates = [datetime.fromisoformat(date).strftime("%d/%m") for date in donnees["dates"]]

    plt.figure(figsize=(12, 6))
    plt.plot(dates, donnees["temp_max"], 'r-o', label='Température max', linewidth=2)
    plt.plot(dates, donnees["temp_min"], 'b-o', label='Température min', linewidth=2)
    plt.fill_between(dates, donnees["temp_min"], donnees["temp_max"], alpha=0.3, color='gray')

    plt.title('Prévisions de température sur 7 jours', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Température (°C)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    for i, (tmax, tmin) in enumerate(zip(donnees["temp_max"], donnees["temp_min"])):
        plt.annotate(f'{tmax}°', (i, tmax), textcoords="offset points", xytext=(0,10), ha='center')
        plt.annotate(f'{tmin}°', (i, tmin), textcoords="offset points", xytext=(0,-15), ha='center')

    plt.show()


def main():
    latitude, longitude = 48.8566, 2.3522
    print("🌤️  Récupération des données météo...")
    donnees = appeler_api_meteo(latitude, longitude)

    if not donnees:
        print("❌ Impossible de récupérer les données météo")
        return

    print("📊 Analyse des données...")
    analyse = analyser_donnees_meteo(donnees)
    if "erreur" in analyse:
        print(f"❌ Erreur d'analyse: {analyse['erreur']}")
        return

    print("\n📈 Résultats:")
    print(f"Période: du {analyse['periode']['debut']} au {analyse['periode']['fin']}")
    print(f"Température max moyenne: {analyse['temperatures']['max_moyenne']}°C")
    print(f"Température min moyenne: {analyse['temperatures']['min_moyenne']}°C")
    print(f"Précipitations totales: {analyse['precipitations']['total_mm']} mm")
    print(f"Jours avec pluie: {analyse['precipitations']['jours_avec_pluie']}")

    print("\n💾 Sauvegarde des résultats...")
    sauvegarder_resultats(analyse)

    print("\n📊 Affichage du graphique...")
    afficher_graphique_temperature(analyse)


if __name__ == "__main__":
    main()
