(() => {
  const panel = document.getElementById('runtime-live-data-normalization');
  if (!panel) throw new Error('Live Data Normalization Pipeline panel missing');
  if (!panel.innerText.includes('source_url')) throw new Error('source_url missing');
  return true;
})();
