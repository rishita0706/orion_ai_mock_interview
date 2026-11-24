# ORION Dataset Directory

Place your labelled audio files here for custom model training.

## Folder Structure

```
dataset/
├── weak/       ← Audio files of weak/poor interview answers
├── average/    ← Audio files of average interview answers  
└── strong/     ← Audio files of strong/excellent interview answers
```

## Supported formats
`.wav`, `.mp3`, `.webm`

## Labelling guide
- **weak**: Short answers, off-topic, no examples, many fillers, low confidence
- **average**: strong but lacks depth/structure, some fillers
- **strong**: Well-structured (STAR method), specific examples, confident delivery

## Training
Once you have files in all three folders, run:
```bash
cd orion/backend
source venv/bin/activate
python ml/train_custom_model.py
```
