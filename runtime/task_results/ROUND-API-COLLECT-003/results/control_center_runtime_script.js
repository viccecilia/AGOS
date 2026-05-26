(() => {
  const panel = document.getElementById('runtime-live-collection-runner');
  if (!panel) throw new Error('Read-Only Live Collection Runner panel missing');
  if (!panel.innerText.includes('blocked')) throw new Error('blocked status missing');
  return true;
})();
