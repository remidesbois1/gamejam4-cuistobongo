# Modèle `bongo-v1`

Agent PPO à actions masquées entraîné sur le jeu complet de Cuisto Bongo
(branche `reinforcementLearning`) : 1,45 milliard de décisions en ~9 h sur une
NVIDIA A100-SXM4-80GB (RunPod, ~16 $), 57 000 décisions/s, graine 1.
Schéma d'observation `CuistoBongo-v1` (577 valeurs), 24 actions masquées.

| Fichier | Contenu |
| --- | --- |
| `model.pt` | Meilleur checkpoint (1,45 Md de décisions), à regarder ou évaluer |
| `config.json` | Configuration complète d'entraînement et résultats |
| `evaluation-40games.json` | Évaluation détaillée : 40 parties inédites, moteur de référence |

## Regarder

```powershell
uv sync --extra train
uv run python -m rl.watch --player models/bongo-v1/model.pt --speed 2
```

Aucun GPU n'est nécessaire. La partie se joue dans le vrai jeu (fenêtre, sons) ;
l'agent presse les touches comme un joueur. `--speed 1` à `--speed 8` règle la
vitesse, `--stochastic` échantillonne les actions, `--seed N` change la partie.
Dans la fenêtre : Espace pause, ↑/↓ vitesse, N nouvelle partie, Échap quitter.

## Évaluer

```powershell
uv run python -m rl.evaluate --player models/bongo-v1/model.pt --games 40 --seed 700000 --limit 12600
```

Moteur de référence headless (mêmes règles que le jeu graphique, vérifié tick
par tick — voir `doc/rl.md`), 40 graines jamais vues à l'entraînement, parties
complètes jusqu'au game over (coupées à 21 min), politique déterministe.

## Résultats

| Joueur | Score | Vagues validées | Pizzas | Morts | Game over |
| --- | --- | --- | --- | --- | --- |
| Hasard | −417 ± 71 | 0 | 0 | 0,15 | 40 / 40 |
| Bot scripté (`rl/baselines.py`) | 621 ± 466 | 1,6 | 12,4 | 5,2 | 40 / 40 |
| **`bongo-v1`** | **18 321 ± 3 663** | **13,1 ± 2,2** | **253 ± 48** | 9,1 | **3 / 40** |

37 parties sur 40 étaient encore vivantes à la coupure de 21 minutes (vagues 13
à 15 validées). Le meilleur score humain honnête du scoreboard du jeu est
2 294 points (vague 4).

Chronologie complète de l'entraînement, courbe d'apprentissage et analyse :
[`presentation/Rapport-CuistoBongo-IA.pdf`](../../presentation/Rapport-CuistoBongo-IA.pdf).

## Reprendre l'entraînement

Le run a été interrompu à 1,45 Md de décisions sur les 2 Md prévus (solde GPU
épuisé) et la courbe montait encore. Pour continuer depuis ce modèle :

```powershell
uv run python -m rl.train --output runs/bongo-v2 --resume models/bongo-v1/model.pt --timesteps 2000000000 --seed 1
```

(réseau, optimiseur, normalisations et compteur de décisions restaurés ; le
checkpoint complet avec optimiseur est `step_1450180608.pt` sur le volume du
pod RunPod `cuisto-rl-1`).
