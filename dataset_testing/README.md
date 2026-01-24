# Dataset Testing

Ce dossier contient les outils pour envoyer des données de test à l'API Carmen.

## Fichiers

- `test_requests.json` : Fichier JSON contenant les requêtes de test avec différentes dates
- `send_test_requests.py` : Script Python pour envoyer toutes les requêtes séquentiellement

## Prérequis

Le script nécessite la bibliothèque `requests` :

```bash
pip install requests
```

## Utilisation

1. **Assurez-vous que le serveur Carmen est démarré** :
   ```bash
   uvicorn app.server:app --reload
   ```

2. **Modifiez `test_requests.json` si nécessaire** pour ajuster les données de test

3. **Exécutez le script** :
   ```bash
   python dataset_testing/send_test_requests.py
   ```
   
   Ou directement :
   ```bash
   cd dataset_testing
   python send_test_requests.py
   ```

## Format du fichier JSON

Le fichier `test_requests.json` contient un tableau d'objets, chacun avec :
- `date` : Date ISO format (YYYY-MM-DDTHH:MM:SS) pour le paramètre `test_date`
- `body` : Corps de la requête avec les données des capteurs

Exemple :
```json
{
  "date": "2024-01-15T08:00:00",
  "body": {
    "humidity": 70,
    "light": 1200,
    "temperature": 22,
    "plant_id": "basil-001",
    "plant_type": "basil"
  }
}
```

## Comportement du script

- Le script envoie les requêtes **séquentiellement** (une après l'autre)
- Il **attend la réponse** de chaque requête avant d'envoyer la suivante
- Affiche le statut de chaque requête en temps réel
- Affiche un résumé à la fin avec les statistiques

## Personnalisation

Vous pouvez modifier :
- `API_URL` dans `send_test_requests.py` pour changer l'URL de l'API
- `REQUEST_DELAY` pour ajuster le délai entre les requêtes (par défaut 0.5 secondes)
- `test_requests.json` pour ajouter/modifier les requêtes de test
