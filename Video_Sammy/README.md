@runtime 6:12
@fps 30
@output moog_piece.mp4
@audio ~/Audio/moog_piece.mp3
@compression hevc crf=30 preset=slow

@images {
  source: ~/ScreenArt/TransformedImages
  filter: grade=A
  shuffle: true
}

@transformers {
  voronoi(cells=80, blend=0.6)
  kaleidoscope(segments=8)
  oilpainting(radius=4)
}

# Generative section — pick images, apply random transformers, 8s slides
0:00..2:30 generative {
  slide_duration: 8s
  crossfade: 1.5s
  transformer_probability: 0.7
}

# Scored section — exact timing
2:30 image=mandala_042.jpg transformer=kaleidoscope(segments=12) duration=15s
2:45 crossfade 2s
2:47 image=lojong_017.jpg transformer=voronoi(cells=120, blend=0.8) duration=20s
3:07 crossfade 1s
3:08 generative until=5:45 { slide_duration: 6s }
5:45 image=peace_003.jpg hold=until_end fade_out=3s
