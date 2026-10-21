(function() {
  const grid = document.getElementById('grid');
  const lb = document.getElementById('lightbox');
  const lbImg = document.getElementById('lb-img');
  const lbName = document.getElementById('lb-filename');
  const lbClose = document.getElementById('lb-close');
  const lbHeart = document.getElementById('lb-heart');
  const lbHeartSvg = document.getElementById('lb-heart-svg');
  let currentFile = null;

  // Initial hearted state comes from server-rendered DOM (the .hearted class)
  let hearted = new Set(
    Array.from(grid.querySelectorAll('.tile.hearted'))
      .map(el => el.dataset.file)
  );

  function setHeartedUI(file, isOn) {
    const tile = grid.querySelector('.tile[data-file="' + CSS.escape(file) + '"]');
    if (tile) tile.classList.toggle('hearted', isOn);
    if (file === currentFile) {
      lbHeartSvg.setAttribute('fill', isOn ? '#ff5577' : 'none');
    }
  }

  // Open lightbox on tile tap
  grid.addEventListener('click', (e) => {
    const tile = e.target.closest('.tile');
    if (!tile) return;
    currentFile = tile.dataset.file;
    lbImg.src = '/images/' + encodeURIComponent(currentFile);
    lbName.textContent = currentFile;
    lbHeartSvg.setAttribute('fill', hearted.has(currentFile) ? '#ff5577' : 'none');
    lb.classList.add('open');
  });

  function closeLightbox() {
    lb.classList.remove('open');
    lbImg.src = '';
    currentFile = null;
  }

  lbClose.addEventListener('click', closeLightbox);
  lb.addEventListener('click', (e) => { if (e.target === lb) closeLightbox(); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLightbox();
  });

  // Heart toggle
  lbHeart.addEventListener('click', () => {
    if (!currentFile) return;
    const isOn = hearted.has(currentFile);
    const endpoint = isOn ? '/api/unheart' : '/api/heart';
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: currentFile })
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.ok) {
        if (isOn) hearted.delete(currentFile);
        else hearted.add(currentFile);
        setHeartedUI(currentFile, !isOn);
      } else {
        console.error('heart toggle failed', resp);
      }
    })
    .catch(e => console.error('heart fetch failed', e));
  });
})();
