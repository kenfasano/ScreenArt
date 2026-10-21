#!/opt/homebrew/bin/zsh
mkdir -p ~/Scripts/ScreenArt/InputSources/Data/ && \
for i in {1..150}; do
  curl -L -o ~/Scripts/ScreenArt/InputSources/Data/HebrewPsalms/psalm_$i.html \
  "https://www.die-bibel.de/en/bible/BHS/PSA.$i";
done
